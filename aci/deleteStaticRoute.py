#!/usr/bin/env python3
'''
    This script configure a static route associated to a L3Out.

    Examples:
    # ./deleteStaticRoute.py -n FW1:dmz -t Prod -s 1.3.3.0/24
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -n STRING  node (i.e. FW1:dmz)')
    print('  -t STRING  tenant')
    print('  -s STRING  subnet (i.e. 10.0.0.0/8)')
    sys.exit(1)

def main():
    debug = False
    tenant = None
    node_name = None
    subnet = None

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
        logger.error('invalid config.yaml file: missing apic_ip, apic_username, apic_password or domain_l3')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vn:t:s:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-n':
            node_name = arg
        elif opt == '-t':
            tenant = arg
        elif opt == '-s':
            subnet = arg
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not node_name:
        logger.error('node not specified')
        sys.exit(1)
    if not tenant:
        logger.error('tenant not specified')
        sys.exit(1)
    if not subnet:
        logger.error('subnet not specified')
        sys.exit(1)
    l3_out = f'L3OUT_{tenant}'

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    # Checking if L3Out exists
    total, l3outs = getL3Outs(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, name = l3_out)
    if total == 0:
        sys.exit(0)

    # Checking if Node Profile exists
    total, l3outs_nodes = getL3OutNodeProfiles(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3_out, name = node_name)
    if total == 0:
        sys.exit(0)

    # Checking if node is configured
    total, nodes = getStaticL3OutConfiguredNodes(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3_out, node_name = node_name)
    if total == 0:
        sys.exit(0)

    for node in nodes:
        path = node['l3extRsNodeL3OutAtt']['attributes']['tDn']
        total, routes = getStaticRoutes(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3_out, node_name = node_name, path = path, network = subnet)
        if total == 0:
            sys.exit(0)
        # Deleting the static route
        if not deleteStaticRoute(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, l3out = l3_out, node_name = node_name, path = path, network = subnet):
            logger.error(f'failed to delete static route from path {path}')
            sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
