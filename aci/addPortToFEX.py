#!/usr/bin/env python3
'''
    This script configure one or more ports from a Fex to be used by a
    single-homed or multi-home device (active-standby, PC or vPC). Then a VLAN
    must be associated with the EPG using the addVLANToEPG.py script.

    Examples:
    # ./addPortToFEX.py -n ESXi01:mgmt -f FEX_Leaf102:Fex101 -p 1/31 -T device
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -n STRING  Connected device (i.e. ESXi02:iLO)')
    print('  -F STRING  Fex Profile Name (i.e. FEX_Leaf102:Fex101, must be repeated with -t)')
    print('  -d STRING  Interface Description (optional)')
    print('  -t STRING  vpc (optional)')
    print('  -T STRING  device|server')
    print('  -a STRING  active|nosuspend|static (mandatory with -t)')
    print('  -p STRING  port (i.e. 1/15)')
    print('  -f         Force: if policy group exists then overwrite it')
    sys.exit(1)

def main():
    debug = False
    fex_profile_names = []
    description = None
    device_type = None
    port = None
    name = None
    po_type = None
    po_protocol = None
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
        aep_l2 = config['aep_l2']
    except:
        logger.error('invalid config.yaml file: missing apic_ip, apic_username, apic_password or aep_l2')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vfF:d:T:t:a:p:n:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-f':
            force = True
        elif opt == '-n':
            name = arg
        elif opt == '-F':
            fex_profile_names.append(arg)
        elif opt == '-T':
            device_type = arg
        elif opt == '-t':
            po_type = arg
        elif opt == '-a':
            po_protocol = arg
        elif opt == '-d':
            description = arg
        elif opt == '-p':
            port = arg
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not fex_profile_names:
        logger.error('fex name not specified')
        sys.exit(1)
    if not port:
        logger.error('port not specified')
        sys.exit(1)
    if not device_type:
        logger.error('device_type not specified')
        sys.exit(1)
    if not name:
        logger.error('name not specified')
    if po_type and po_type not in ['vpc']:
        logger.error('po_type is not valid')
        sys.exit(1)
    if po_protocol and po_protocol not in ['active', 'nosuspend', 'static']:
        logger.error('po_protocol is not valid')
        sys.exit(1)
    if not description:
        description = name

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    if not po_type:
        # Configuring single port
        if device_type == 'server':
            group = 'SinglePort_Server'
        elif device_type == 'device':
            group = 'SinglePort_Device'
        else:
            logging.error(f'device type {device_type} not supported')
            sys.exit(1)
    else:
        # Configuring a vPC
        group = f'vPC_{name}'
        attributes = {
            'lagT': 'node'
        }
        po_description = f'Virtual Port-Channel to {name}'
        if device_type == 'device':
            policies = ['CDP_On', 'LLDP_On', 'BPDU_Guard']
        elif device_type == 'server':
            policies = ['CDP_Off', 'LLDP_Off', 'BPDU_Guard']
        else:
            logging.error(f'device type {device_type} not supported')
            sys.exit(1)
        if po_protocol == 'active':
            policies.append('LACP_Active')
        elif po_protocol == 'nosuspend':
            policies.append('LACP_No_Suspend')
        elif po_protocol == 'static':
            policies.append('Static')
        else:
            logging.error(f'po_protocol {po_protocol} not supported')
            sys.exit(1)

        # Checking if interface policy group exists
        total, interface_policy_groups = getInterfacePolicyGroups(ip = apic_ip, token = token, cookies = cookies, name = group, class_name = 'infraAccBndlGrp')
        if total is 0 or force:
            # Adding the policy group (port-channel)
            if not addInterfacePolicyGroup(ip = apic_ip, token = token, cookies = cookies, name = group, policies = policies, aep = aep_l2, description = po_description, attributes = attributes, class_name = 'infraAccBndlGrp'):
                logging.error(f'failed to add port-channel {name}')
                sys.exit(1)

    # Checking if Fex profile exists
    for fex_profile_name in fex_profile_names:
        total, fex_profiles = getFexProfile(ip = apic_ip, token = token, cookies = cookies, name = fex_profile_name)
        if total is 0:
            logging.error(f'Fex profile {fex_profile_name} not found')
            sys.exit(1)

        # Checking if interface selector block exists
        total, interface_selector_blocks = getInterfaceSelectorBlocks(ip = apic_ip, token = token, cookies = cookies, profile = fex_profile_name, name = port, fex = True)
        if total is 0:
            # Adding interface selector block
            if not addInterfaceSelectorBlock(ip = apic_ip, token = token, cookies = cookies, profile = fex_profile_name, selector = name, name = port, description = description, fex = True, group = group):
                logging.error(f'failed to create interface selector block with {port}')
                sys.exit(1)
        else:
            logging.warning(f'port {port} is already configured on Fex {fex_profile_name}')
            continue

if __name__ == '__main__':
    main()
    sys.exit(0)
