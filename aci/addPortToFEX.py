#!/usr/bin/env python3
'''
    This script configure one or more ports from a Fex to be used by a
    single-homed or multi-home device (active-standby, PC or vPC). Then a VLAN
    must be associated with the EPG using the addVLANToEPG.py script.

    Examples:
    # ./addPortToFEX.py -v -n FEX_Leaf102:Fex101 -p 1/15 -T device|server|vPC_ESXi03:mgmt
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -n STRING  Connected device (i.e. ESXi02:iLO)')
    print('  -f STRING  Fex Profile Name (i.e. FEX_Leaf102:Fex101)')
    print('  -d STRING  Interface Description (optional)')
    print('  -T STRING  device|server')
    print('  -p STRING  port (i.e. 1/15, can be repeated)')
    sys.exit(1)

def main():
    debug = False
    fex_profile_name = None
    description = None
    device_type = None
    ports = []
    name = None

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
        opts, args = getopt.getopt(sys.argv[1:], 'vf:d:T:p:n:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-n':
            name = arg
        elif opt == '-f':
            fex_profile_name = arg
        elif opt == '-T':
            device_type = arg
        elif opt == '-d':
            description = arg
        elif opt == '-p':
            ports.append(arg)
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not fex_profile_name:
        logger.error('fex name not specified')
        sys.exit(1)
    if not ports:
        logger.error('port not specified')
        sys.exit(1)
    if not device_type:
        logger.error('device_type not specified')
        sys.exit(1)
    if not name:
        logger.error('name not specified')
    if not description:
        description = name

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    if device_type == 'server':
        group = 'SinglePort_Server'
    elif device_type == 'device':
        group = 'SinglePort_Device'
    else:
        # Device type not recognized, looking for an interface policy group (PC/vPC)
        total, interface_policy_groups = getInterfacePolicyGroups(ip = apic_ip, token = token, cookies = cookies, name = group, class_name = 'infraAccPortGrp')
        if total is 0:
            logging.error(f'interface policy group {group} does not exist')
            sys.exit(1)
        group = device_type

    # Checking if Fex profile exists
    total, fex_profiles = getFexProfile(ip = apic_ip, token = token, cookies = cookies, name = fex_profile_name)
    if total is 0:
        logging.error(f'Fex profile not found')
        sys.exit(1)

    # Checking if interface selector block exists
    for port in ports:
        total, interface_selector_blocks = getInterfaceSelectorBlocks(ip = apic_ip, token = token, cookies = cookies, profile = fex_profile_name, name = port, fex = True)
        if total is 0:
            # Adding interface selector block
            if not addInterfaceSelectorBlock(ip = apic_ip, token = token, cookies = cookies, profile = fex_profile_name, selector = name, name = port, description = description, fex = True, group = group):
                logging.error(f'failed to create interface selector block with {port}')
                sys.exit(1)
        else:
            logging.error(f'port {port} is already configured on Fex {fex_profile_name}')
            sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
