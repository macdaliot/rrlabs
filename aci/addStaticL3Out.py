#!/usr/bin/env python3
'''
    This script configure a L3Out.

    Examples:
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -d STRING  Interface Profile Description (optional)')
    print('  -n STRING  name (i.e. FW1:dmz)')
    print('  -t STRING  tenant')
    print('  -f         Force: if interface profile exists then overwrite it')
    sys.exit(1)

def main():
    debug = False
    force = False
    description = None
    tenant = None
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
        domain_l3 = config['domain_l3']
    except:
        logger.error('invalid config.yaml file: missing apic_ip, apic_username, apic_password or domain_l3')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vfd:n:t:')
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
        if not addL3Out(ip = apic_ip, token = token, cookies = cookies, name = l3out_name, description = l3out_description, tenant = tenant, vrf = tenant, domain = domain_l3):
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


if __name__ == '__main__':
    main()
    sys.exit(0)



# Nome Node Profile
# Nodo (pod/leaf)
# Router ID del nodo
# IP del nodo
# IP del nodo (VIP/HSRP)
# Single PC/VPC
# Access/Trunk
# VLAN



#
# interface profile
#
# ethod: POST
# url: https://10.1.24.1/api/node/mo/uni/tn-Prod/out-AAANAME/lnodep-AAANAME/lifp-AAANAME.json
# payload{"l3extLIfP":{"attributes":{"dn":"uni/tn-Prod/out-AAANAME/lnodep-AAANAME/lifp-AAANAME","name":"AAANAME","descr":"AAADESC","rn":"lifp-AAANAME","status":"created"},"children":[{"l3extRsPathL3OutAtt":{"attributes":{"dn":"uni/tn-Prod/out-AAANAME/lnodep-AAANAME/lifp-AAANAME/rspathL3OutAtt-[topology/pod-1/paths-101/pathep-[eth1/43]]","mac":"00:22:BD:F8:19:FF","ifInstT":"ext-svi","encap":"vlan-1123","addr":"1.2.3.4/24","tDn":"topology/pod-1/paths-101/pathep-[eth1/43]","rn":"rspathL3OutAtt-[topology/pod-1/paths-101/pathep-[eth1/43]]","status":"created"},"children":[{"l3extIp":{"attributes":{"addr":"1.2.3.1/24","status":"created"},"children":[]}}]}}]}}
# response: {"totalCount":"0","imdata":[]}
# timestamp: 15:56:00 DEBUG
#
# link L3Out with alll EPGs of VRF Prod
#
#
# Static route
#
# method: POST
# url: https://10.1.24.1/api/node/mo/uni/tn-Prod/out-AAANAME/lnodep-AAANAME/rsnodeL3OutAtt-[topology/pod-1/node-101]/rt-[10.1.2.3/30].json
# payload{"ipRouteP":{"attributes":{"dn":"uni/tn-Prod/out-AAANAME/lnodep-AAANAME/rsnodeL3OutAtt-[topology/pod-1/node-101]/rt-[10.1.2.3/30]","ip":"10.1.2.3/30","rn":"rt-[10.1.2.3/30]","status":"created"},"children":[{"ipNexthopP":{"attributes":{"dn":"uni/tn-Prod/out-AAANAME/lnodep-AAANAME/rsnodeL3OutAtt-[topology/pod-1/node-101]/rt-[10.1.2.3/30]/nh-[1.2.3.7]","nhAddr":"1.2.3.7","pref":"1","rn":"nh-[1.2.3.7]","status":"created"},"children":[]}}]}}
# response: {"totalCount":"0","imdata":[]}
