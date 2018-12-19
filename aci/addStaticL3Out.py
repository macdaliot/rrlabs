#!/usr/bin/env python3
'''
    This script configure a L3Out.

    Examples:
    # ./addStaticL3Out.py -n FW1:dmz -t Prod -m trunk -i 1143 -I 10.0.0.1/24 Leaf101,10.0.0.2/24,1/37 -b
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -d STRING  Interface Profile Description (optional)')
    print('  -b         Bind existent L3 BD to the L3 Out')
    print('  -n STRING  name (i.e. FW1:dmz)')
    print('  -t STRING  tenant')

    print('  -m STRING  trunk|access')
    print('  -i INTEGER VLAN ID')
    print('  -I STRING  VIP IP Address (i.e. 10.0.0.1/24)')

    print('  -l STRING  Leaf Name,RID,IP,port|group (i.e.:')
    print('             Leaf101,10.0.0.2/24,1/15, or')
    print('             Leaf101,10.0.0.2/24,vPC_FW)')

    print('  -f         Force: if interface profile exists then overwrite it')
    sys.exit(1)

def main():
    debug = False
    force = False
    description = None
    tenant = None
    name = None
    mode = None
    vlan = None
    vip_ip_address = None
    leafs = []
    bind = False

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
        domain_l3 = config['domain_l3']
    except:
        logger.error('invalid config.yaml file: missing apic_ip, apic_username, apic_password or domain_l3')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vfbd:n:t:m:i:a:V:I:l:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-d':
            description = arg
        elif opt == '-n':
            name = arg
        elif opt == '-t':
            tenant = arg
        elif opt == '-f':
            force = True
        elif opt == '-b':
            bind = True
        elif opt == '-m':
            mode = arg
        elif opt == '-i':
            vlan = arg
        elif opt == '-a':
            port_type = arg
        elif opt == '-I':
            vip_ip_address = arg
        elif opt == '-g':
            group = arg
        elif opt == '-p':
            port = arg
        elif opt == '-l':
            try:
                leafs.append({
                    'name': arg.split(',')[0],
                    'ip': arg.split(',')[1],
                    'port': arg.split(',')[2]
                })
            except Exception as err:
                logger.error('cannot parse Leaf Name, IP and port or policy group')
                sys.exit(1)
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not name:
        logger.error('name not specified')
        sys.exit(1)
    if not tenant:
        logger.error('tenant not specified')
        sys.exit(1)
    if not vip_ip_address:
        logger.error('VIP IP address specified')
        sys.exit(1)
    if len(leafs) < 1:
        logger.error('need at least one leaf')
    l3out_name = f'L3OUT_{tenant}'
    l3out_description = f'Static L3Out for VRF {tenant}'
    l3out_interface_description = f'Logical (SVI) and physical (single/PC/vPC) interfaces facing {name}'
    if not description:
        description = f'Static routing to {name}'

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    # Checking if L3Out exists
    total, l3outs = getL3Outs(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, name = l3out_name)
    if total == 0 or force:
        # Adding interface profile
        if not addStaticL3Out(ip = apic_ip, token = token, cookies = cookies, name = l3out_name, description = l3out_description, tenant = tenant, vrf = tenant, domain = domain_l3):
            logging.error(f'failed to create L3Out {l3out_name}')
            sys.exit(1)

    # Checking if Node Profile exists
    total, l3outs_nodes = getL3OutNodeProfiles(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3out_name, name = name)
    if total == 0 or force:
        # Adding node profile
        if not addL3OutNodeProfile(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3out_name, name = name, description = description):
            logging.error(f'failed to create L3Out node profile {name}')
            sys.exit(1)

    # Checking if Logical Interface profile exists
    total, l3outs_interfaces = getL3OutNodeInterfaceProfiles(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3out_name, node = name, name = 'ports')
    if total == 0 or force:
        # Adding interface profile
        if not addL3OutNodeInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3out_name, name = 'ports', description = l3out_interface_description, node = name):
            logging.error(f'failed to create L3Out node profile {l3out_name}')
            sys.exit(1)

    for leaf in leafs:
        leaf_id = getLeafID(ip = apic_ip, token = token, cookies = cookies, name = leaf['name'])
        vip_mac_address = '00:22:BD:00:0{}:{}'.format(str(leaf_id)[0], str(leaf_id)[1:3])
        router_id = f'192.168.20.{leaf_id}'

        if '/' in leaf['port']:
            # This is a single port (i.e. 1/25)
            port_path = getPathFromLeafPort(ip = apic_ip, token = token, cookies = cookies, name = leaf['name'], port = leaf['port'])
            if not port_path:
                logging.error(f'Port {leaf["port"]} not found in Leaf {leaf["name"]}')
                sys.exit(1)
            # Checking if SVI exists
            total, svis = getStaticL3OutSVI(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3out_name, node_name = name, interface_name = 'ports', path = port_path)
            if total == 0:
                # Adding the SVI
                if not addStaticL3OutSVI(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, path = path, vip_mac_address = vip_mac_address, vlan = vlan, leaf_ip = leaf['ip'], vip_ip_address = vip_ip_address, mode = mode, l3out = l3out_name, node_name = name, name = 'ports'):
                    logging.error('failed to create SVI on path {path}')
                    sys.exit(1)

            node_path = getPathFromLeafName(ip = apic_ip, token = token, cookies = cookies, name = leaf['name'])
            if not node_path:
                logging.error(f'Node {leaf["name"]} not found')
                sys.exit(1)

            # Checking if node exists
            total, nodes = getStaticL3OutConfiguredNodes(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3out_name, node_name = name, path = node_path)
            if total == 0:
                # Adding physical node path
                if not addStaticL3OutConfiguredNodes(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3out_name, node_name = name, path = node_path, router_id = router_id):
                    logging.error(f'cannot add physical path {path} for L3Out')
                    sys.exit(1)

    if bind:
        total, bds = getBDs(ip = apic_ip, token = token, cookies = cookies, tenant = tenant)
        for bd in bds:
            has_subnet = False
            has_l3out = False
            try:
                bd_name = bd['fvBD']['attributes']['name']
                for children in bd['fvBD']['children']:
                    if 'fvSubnet' in children:
                        # BD has a subnet
                        has_subnet = True
                    elif 'fvRsBDToOut' in children:
                        # BD has a L3Out
                        if children['fvRsBDToOut']['attributes']['tnL3extOutName'] == f'L3OUT_{tenant}':
                            has_l3out = True
                if has_subnet and not has_l3out:
                    # BD has a subnet but is missing the L3Out
                    if not bindBDtoL3Out(ip = apic_ip, token = token, cookies = cookies, name = bd_name, tenant = tenant, l3out = f'L3OUT_{tenant}'):
                        logger.error(f'failed to bind L3Oout to BD {bd_name}')
                        sys.exit(1)
            except Exception as err:
                # BD has no children (no subnet, no L3Out)
                continue

if __name__ == '__main__':
    main()
    sys.exit(0)
