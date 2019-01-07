#!/usr/bin/env python3
'''
    This script check if a port is used in any tenant/app/EPGs. If the port is not used, the port is deconfigured.

    Examples:
    # ./deleteSinglePort.py -l Leaf102 -p 1/37 -f 101
'''

import getopt, logging, sys, time, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -d         dry run (do not delete)')
    print('  -f         force (delete without asking)')
    print('  -l STRING  leaf')
    print('  -p STRING  port (i.e. 1/15)')
    print('  -F INTEGER FEX ID (i.e. 101, optional)')
    sys.exit(1)

def main():
    debug = False
    leaf = None
    port = None
    fex = None
    delete = True
    force = False

    # Configure logging
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    # Reading config.yaml file
    with open('config.yaml', 'r') as f:
        try:
            config = yaml.load(f)
        except Exception as err:
            logger.error('exception while reading config.yaml file', exc_info = debug)
    try:
        apic_ip = config['apic_ip']
        apic_username = config['apic_username']
        apic_password = config['apic_password']
    except:
        logger.error('invalid config.yaml file: missing apic_ip, apic_username or apic_password')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vdfl:p:F:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-d':
            delete = False
        elif opt == '-f':
            force = True
        elif opt == '-l':
            leaf = arg
        elif opt == '-p':
            port = arg
        elif opt == '-F':
            fex = arg
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not leaf:
        logger.error('leaf not specified')
        sys.exit(1)
    if not port:
        logger.error('port not specified')
        sys.exit(1)

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    # Finding the path
    path = getPathFromLeafPort(ip = apic_ip, token = token, cookies = cookies, name = leaf, port = port, fex = fex)
    if not path:
        logging.error(f'cannot find path for {leaf}/{fex}/{port}')
        sys.exit(1)

    # Get Leaf ID and POD
    leaf_path = getPathFromLeafName(ip = apic_ip, token = token, cookies = cookies, name = leaf)
    if not leaf_path:
        logging.error(f'cannot find leaf {leaf}')
        sys.exit(1
        )

    # Get EPGs from path
    total, epgs = getEPGsFromPath(ip = apic_ip, token = token, cookies = cookies, leaf_path = leaf_path, port = port, fex = fex)
    if total > 0:
        # Port is used by EPGs
        used_by = []
        for epg in epgs:
            used_by.append(epg['pconsResourceCtx']['attributes']['ctxDn'])
        logging.error('port is used by: {}'.format(', '.join(used_by)))
        sys.exit(1)

    # is the port used by a PC/vPC?
    cfg = getPortCfgFromPath(ip = apic_ip, token = token, cookies = cookies, leaf_path = leaf_path, port = port, fex = fex)
    if cfg['bundleIndex'] != 'unspecified':
        logging.error(f'port is used by {cfg["bundleIndex"]}')
        sys.exit(1)

    # any VLAN?
    if cfg['allowedVlans']:
        logging.error(f'port is using VLANs {cfg["allowedVlans"]}')
        sys.exit(1)

    # is up?
    if not force and cfg['operSt'] == 'up':
        confirm = input(f'Port {leaf}:{fex}:{port} is up. Continue? [no|yes]')
        if confirm != 'yes':
            print('Aborting...')
            sys.exit(0)

    if delete and fex:
        fex_profile_name = f'FEX_{leaf}:Fex{fex}'
        # Checking if port is used
        total, interface_selector_blocks = getInterfaceSelectorBlocks(ip = apic_ip, token = token, cookies = cookies, profile = fex_profile_name, name = port, fex = True)
        if total != 0:
            for interface_selector_block in interface_selector_blocks:
                delete_selector = False
                selector = interface_selector_block['infraPortBlk']['attributes']['dn'].split('/')[3].split('-')[1]
                port_id = interface_selector_block['infraPortBlk']['attributes']['name']
                total_blocks, unused = getInterfaceSelectorBlocks(ip = apic_ip, token = token, cookies = cookies, profile = fex_profile_name, selector = selector, fex = True)
                if total_blocks == 1:
                    delete_selector = True
                if not force:
                    confirm = input(f'Removing port {port} (id={port_id}) from interface profile FEX_{leaf}:Fex{fex}/{selector}. Continue? [no|yes]')
                    if confirm != 'yes':
                        print('Aborting...')
                        sys.exit(0)
                    if delete_selector:
                        confirm = input(f'Removing also FEX_{leaf}:Fex{fex}/{selector}. Continue? [no|yes]')
                        if confirm != 'yes':
                            print('Aborting...')
                            sys.exit(0)
                # Delete the interface from the Leaf Interface Profile
                if not deleteInterfaceSelectorBlock(ip = apic_ip, token = token, cookies = cookies, name = port_id, profile = fex_profile_name, fex = True, selector = selector, delete_selector = delete_selector):
                    logging.error('failed to delete port from FEX')
                    sys.exit(1)

    if delete and not fex:
        interface_profile = getInterfaceProfileFromPortAndLeaf(ip = apic_ip, token = token, cookies = cookies, port = port, leaf = leaf)
        if interface_profile:
            # Unbind interface_profile from leaf
            if not force:
                confirm = input(f'Unbinding profile {interface_profile} from leaf {leaf}. Continue? [no|yes]')
                if confirm != 'yes':
                    print('Aborting...')
                    sys.exit(0)
            if not unbindSwitchProfileFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf, interface_profile = interface_profile):
                logging.error('failed to unbind interface profile from leaf')
                sys.exit(1)

            # Counting how many switch profiles are bound to the interface profile
            time.sleep(1)
            total, switch_profiles = getSwitchProfilesFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = interface_profile)
            if total == 0:
                # Interface profile is unused
                if not force:
                    confirm = input(f'Deleting unused profile {interface_profile}. Continue? [no|yes]')
                    if confirm != 'yes':
                        print('Aborting...')
                        sys.exit(0)

                if not deleteInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = interface_profile):
                    logging.error('failed to delete interface profile')
                    sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
