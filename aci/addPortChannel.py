#!/usr/bin/env python3
'''
    This script configure a port-channe or a virtual port-channel with one or
    more ports. Then a VLAN must be associated with the EPG using the
    addVLANToEPG.py script.

    Examples:
    # ./addPortChannel.py -t pc -T device -a active -n ESXi01-mgmt -p 1/15 -l Leaf101_102

'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -t STRING  pc|vpc')
    print('  -T STRING  device|server|switch')
    print('  -a STRING  active|nosuspend|static')
    print('  -n STRING  Connected device name (i.e. ESXi01:mgmt)')
    print('  -l STRING  Leaf profile (i.e. Leaf101_102)')
    print('  -p STRING  Ports (i.e. 1/30, can be repeated)')
    print('  -d STRING  description (optional)')
    print('  -f         Force: if policy group exists then overwrite it')
    sys.exit(1)

def main():
    debug = False
    force = False
    device_name = None
    po_type = None
    device_type = None
    po_protocol = None
    ports = []
    description = None
    policies = []
    attributes = {}
    leaf_profile = None

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
        opts, args = getopt.getopt(sys.argv[1:], 'vft:T:a:n:p:d:l:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-t':
            po_type = arg
        elif opt == '-T':
            device_type = arg
        elif opt == '-a':
            po_protocol = arg
        elif opt == '-d':
            description = arg
        elif opt == '-n':
            device_name = arg
        elif opt == '-l':
            leaf_profile = arg
        elif opt == '-p':
            ports.append(arg)
        elif opt == '-f':
            force = True
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not device_name:
        logger.error('device_name not specified')
        sys.exit(1)
    if not po_type or po_type not in ['pc', 'vpc']:
        logger.error('po_type not specified or not valid')
        sys.exit(1)
    if not device_type or device_type not in ['switch', 'device', 'server']:
        logger.error('device_type not specified')
        sys.exit(1)
    if not po_protocol or po_protocol not in ['active', 'nosuspend', 'static']:
        logger.error('po_protocol not specified')
        sys.exit(1)
    if not ports:
        logger.error('ports not specified')
        sys.exit(1)
    if not leaf_profile:
        logger.error('leaf profile not specified')
        sys.exit(1)
    if device_type == 'switch':
        policies = ['CDP_On', 'LLDP_On', 'BPDU_Forward']
    elif device_type == 'device':
        policies = ['CDP_On', 'LLDP_On', 'BPDU_Guard']
    elif device_type == 'server':
        policies = ['CDP_Off', 'LLDP_Off', 'BPDU_Guard']
    else:
        logging.error(f'device type {device_type} not supported')
        sys.exit(1)
    name = f'PC_{device_name}'
    if po_type == 'vpc':
        attributes['lagT'] = 'node'
        name = f'v{name}'
    port_group_description = f'Port-Channel to {device_name}'
    if po_type == 'vpc':
        port_group_description = f'Virtual {port_group_description}'
    if  description:
        profile_description = description
        interface_description = description
    else:
        profile_description = f'Port-Channel connected to {device_name}'
        if po_type == 'vpc':
            profile_description = f'Virtual {profile_description}'
        interface_description = f'{device_name}'

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    # Checking if switch profile exists
    total, switch_profiles = getSwitchProfiles(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile)
    if total == 0:
        logging.error(f'switch profile {leaf_profile} does not exist')
        sys.exit(1)

    # Checking if interface policy group exists
    total, interface_policy_groups = getInterfacePolicyGroups(ip = apic_ip, token = token, cookies = cookies, name = name, class_name = 'infraAccBndlGrp')
    if total == 0 or force:
        # Adding the policy group (port-channel)
        if not addInterfacePolicyGroup(ip = apic_ip, token = token, cookies = cookies, name = name, policies = policies, aep = aep_l2, description = port_group_description, attributes = attributes, class_name = 'infraAccBndlGrp'):
            logging.error(f'failed to add port-channel {name}')
            sys.exit(1)

    # Checking if interface profile exists
    total, interface_profiles = getInterfaceProfiles(ip = apic_ip, token = token, cookies = cookies, name = device_name)
    if total == 0 or force:
        # Adding interface profile
        if not addInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = device_name, description = profile_description):
            logging.error(f'failed to create interface profile {device_name}')
            sys.exit(1)

    # Checking how many switch profiles are connected to the interface profile
    total, switch_profiles = getSwitchProfileFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = name)
    if total > 1:
        logging.error(f'interface profile {name} is bound to multiple switch profiles')
    elif total == 1:
        connected_leaf = switch_profiles[0]['infraRtAccPortP']['attributes']['tDn'].split('/')[-1][6:]
        if leaf != connected_leaf:
            logging.error(f'interface profile {name} is bound to a different switch profile {connected_leaf}')
            sys.exit(1)
    else:
        # Binding interface profile with the switch profile
        if not bindSwitchProfileToInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile, interface_profile = name):
            logging.error(f'failed to bind switch profile {leaf_profile} to interface profile {name}')
            sys.exit(1)

    # Checking if interface selector exists
    total, interface_selectors = getInterfaceSelectors(ip = apic_ip, token = token, cookies = cookies, profile = device_name, name = 'ports')
    if total == 0 or force:
        # Adding interface selector associated to the policy group
        if not addInterfaceSelector(ip = apic_ip, token = token, cookies = cookies, profile = device_name, name = 'ports', group = name, class_name = 'infraAccBndlGrp'):
            logging.error(f'failed to create interface selector {device_name}')
            sys.exit(1)

    # Checking if interface selector block exists
    for port in ports:
        total, interface_selector_blocks = getInterfaceSelectorBlocks(ip = apic_ip, token = token, cookies = cookies, profile = device_name, selector = 'ports', name = port)
        if total == 0:
            # Adding interface selector block
            if not addInterfaceSelectorBlock(ip = apic_ip, token = token, cookies = cookies, profile = device_name, selector = 'ports', name = port, description = device_name):
                logging.error(f'failed to create interface selector block with {port}')
                sys.exit(1)

    # Associating the interfaces to the policy group

    '''
        if not fex:
            interface profile name = device_name
                interface selector = one or more port
            the script associate all ports to the leaf_profile
    '''

if __name__ == '__main__':
    main()
    sys.exit(0)
