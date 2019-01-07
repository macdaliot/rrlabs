#!/usr/bin/env python3
'''
    This script check if a port is used in any tenant/app/EPGs. If the port is not used, the port is deconfigured.

    Examples:
    # ./deletePortChannel.py -l Leaf101_102 -p 1/37 -F 101
'''

import getopt, logging, re, sys, time, yaml
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
    id_1 = None
    id_2 = None

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

    # Finding the switch IDs
    leafs = []
    try:
        s = re.search(r"^([^0-9]+)([0-9]+)_([0-9]+)$", leaf)
        prefix = s.group(1)
        leafs.append(f'{s.group(1)}{s.group(2)}')
        leafs.append(f'{s.group(1)}{s.group(3)}')
    except Exception as err:
        logging.error(f'cannot parse leaf {leaf}, should be in the form: Leaf103_104')
        sys.exit(1)

    # Finding the interface profile
    interface_profile = getInterfaceProfileFromPortAndLeaf(ip = apic_ip, token = token, cookies = cookies, port = port, leaf = leaf)
    if not interface_profile:
        logging.error(f'cannot find interface profile for {leaf}/{fex}/{port}')
        sys.exit(1)

    # Finding the path
    path = getPathFromPolicyGroup(ip = apic_ip, token = token, cookies = cookies, name = interface_profile)
    if not path:
        logging.error(f'cannot find path for {interface_profile}')
        sys.exit(1)

    # Get EPGs from path
    total, leaves = getEPGsFromInterfaceProfilePath(ip = apic_ip, token = token, cookies = cookies, interface_profile_path = path)
    if total > 0:
        # Port is used by leaf
        for leaf in leaves:
            leaf_id = leaf['pconsNodeDeployCtx']['attributes']['nodeId']
            used_by = []
            for epg in leaf['pconsNodeDeployCtx']['children']:
                used_by.append(epg['pconsResourceCtx']['attributes']['ctxDn'])
            logging.error('port is used in leaf {} by: {}'.format(leaf_id, ', '.join(used_by)))
        sys.exit(1)

    # testing if ports are used
    for l in leafs:
        leaf_path = getPathFromLeafName(ip = apic_ip, token = token, cookies = cookies, name = l)
        if not leaf_path:
            logging.error(f'cannot find leaf {l}')
            sys.exit(1)

        # any VLAN?
        cfg = getPortCfgFromPath(ip = apic_ip, token = token, cookies = cookies, leaf_path = leaf_path, port = port, fex = fex)
        if cfg['allowedVlans']:
            logging.error(f'port is using VLANs {cfg["allowedVlans"]}')
            sys.exit(1)

        # is up?
        if not force and cfg['operSt'] == 'up':
            confirm = input(f'Port {l}:{fex}:{port} is up. Continue? [no|yes]')
            if confirm != 'yes':
                print('Aborting...')
                sys.exit(0)

    if delete and not fex:
        # Counting how many switch profiles are bound to the interface profile
        total, unused = getSwitchProfilesFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = interface_profile, leaf = leaf)
        if total > 0:
            if not force:
                confirm = input(f'Unbinding interface profile {interface_profile} from {leaf}. Continue? [no|yes]')
                if confirm != 'yes':
                    print('Aborting...')
                    sys.exit(0)
            if not unbindSwitchProfileFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf, interface_profile = interface_profile):
                logging.error('failed to unbind interface profile from leaf')
                sys.exit(1)

        # Counting how many switch profiles are bound to the interface profile
        time.sleep(1)
        total, unused = getSwitchProfilesFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = interface_profile, leaf = leaf)
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
