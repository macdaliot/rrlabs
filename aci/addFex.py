#!/usr/bin/env python3
'''
    This script configure a Fex attached to one leaf on one or more ports.

    Examples:
    # ./addFex.py
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -n STRING  Fex Name (i.e. Fex101)')
    print('  -i INT     Fex ID (i.e. 101)')
    print('  -l STRING  Leaf Profile (i.e. Leaf101)')
    print('  -d STRING  description (optional)')
    print('  -p STRING  port facing the Fex (i.e. 1/45, can be repeated)')
    print('  -f         Force: if Fex profile exists then overwrite it')
    sys.exit(1)

def main():
    debug = False
    force = False
    name = None
    id = None
    leaf_profile = None
    description = None
    ports = []

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
        opts, args = getopt.getopt(sys.argv[1:], 'vfn:i:l:d:p:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-n':
            name = arg
        elif opt == '-i':
            id = int(arg)
        elif opt == '-d':
            description = arg
        elif opt == '-l':
            leaf_profile = arg
        elif opt == '-f':
            force = True
        elif opt == '-p':
            ports.append(arg)
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not name:
        logger.error('name not specified')
        sys.exit(1)
    if not leaf_profile:
        logger.error('leaf not specified')
        sys.exit(1)
    if not id or id < 101 or id > 199:
        logger.error('fex id not specified or not between 101 and 199')
        sys.exit(1)
    if not ports:
        logger.error('port not specified')
    fex_profile_name = f'Fex_{leaf_profile}:{name}'
    leaf_profile_name = f'{leaf_profile}:{name}'

    # Setting description
    if not description:
        description = f'Fex {name} connected to Leaf {leaf_profile}'

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    # Checking if Fex profile exists
    total, fex_profiles = getFexProfile(ip = apic_ip, token = token, cookies = cookies, name = fex_profile_name)
    if total == 0 or force:
        # Adding interface selector block
        if not addFexProfile(ip = apic_ip, token = token, cookies = cookies, name = fex_profile_name, description = description):
            logging.error(f'failed to create Fex profile')
            sys.exit(1)

    # Checking if interface profile exists
    total, interface_profiles = getInterfaceProfiles(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile_name)
    if total == 0 or force:
        # Adding interface profile
        if not addInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile_name, description = f'Port-Channel connected to Fex {fex_profile_name}'):
            logging.error(f'failed to create interface profile {leaf_profile_name}')
            sys.exit(1)

    # Checking how many switch profiles are connected to the leaf interface profile
    total, switch_profiles = getSwitchProfileFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile_name)
    if total > 1:
        logging.error(f'Fex profile {name} is bound to multiple switch profiles')
    elif total == 1:
        connected_leaf = switch_profiles[0]['infraRtAccPortP']['attributes']['tDn'].split('/')[-1][6:]
        if leaf_profile != connected_leaf:
            logging.error(f'Fex profile {name} is bound to a different switch profile {connected_leaf}')
            sys.exit(1)
    else:
        # Binding Fex profile with the switch profile
        if not bindSwitchProfileToInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile, interface_profile = leaf_profile_name):
            logging.error(f'failed to bind switch profile {leaf} to fex profile {name}')
            sys.exit(1)

    # Checking if interface selector exists
    total, interface_selectors = getInterfaceSelectors(ip = apic_ip, token = token, cookies = cookies, profile = leaf_profile_name, name = 'fex_ports')
    if total == 0 or force:
        # Adding interface selector associated to the policy group
        if not addInterfaceSelector(ip = apic_ip, token = token, cookies = cookies, profile = leaf_profile_name, name = 'fex_ports', group = name, class_name = 'infraAccBndlGrp', fex_id = id, fex_profile_name = fex_profile_name):
            logging.error(f'failed to create fex interface selector {leaf_profile_name}')
            sys.exit(1)

    # Checking if interface selector block exists
    for port in ports:
        total, interface_selector_blocks = getInterfaceSelectorBlocks(ip = apic_ip, token = token, cookies = cookies, profile = leaf_profile_name, selector = 'fex_ports', name = port)
        if total == 0:
            # Adding interface selector block
            if not addInterfaceSelectorBlock(ip = apic_ip, token = token, cookies = cookies, profile = leaf_profile_name, selector = 'fex_ports', name = port, description = fex_profile_name):
                logging.error(f'failed to create interface selector block with {port}')
                sys.exit(1)


# ethod: POST
# url: https://10.1.24.1/api/node/mo/uni/infra/accportprof-ICCA-Leaf04:Fex107/hports-aaaa-typ-range.json
# payload{"infraHPortS":{"attributes":{"dn":"uni/infra/accportprof-ICCA-Leaf04:Fex107/hports-aaaa-typ-range","name":"aaaa","rn":"hports-aaaa-typ-range","status":"created,modified"},"children":[{"infraPortBlk":{"attributes":{"dn":"uni/infra/accportprof-ICCA-Leaf04:Fex107/hports-aaaa-typ-range/portblk-block2","fromPort":"27","toPort":"27","name":"block2","rn":"portblk-block2","status":"created,modified"},"children":[]}},{"infraRsAccBaseGrp":{"attributes":{"tDn":"uni/infra/fexprof-Fex_ICCA-Leaf04:Fex107/fexbundle-Fex_ICCA-Leaf04:Fex107","fexId":"107","status":"created,modified"},"children":[]}}]}}
# response: {"totalCount":"0","imdata":[]}
# timestamp: 13:10:11 DEBUG


if __name__ == '__main__':
    main()
    sys.exit(0)
