#!/usr/bin/env python3
'''
    This script delete a network in terms of Bridge Domain and EPG.

    Examples:
    # c./deleteNetwork.py -t Tenant -n Prod_Network -q 1531 -v
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -t STRING  Tenant Name')
    print('  -n STRING  Network Name')
    print('  -o         Delete only the subnet (optional)')
    print('  -q INT     VLAN ID (802.1Q)')
    sys.exit(1)

def main():
    debug = False
    name = None
    only_subnet = False

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
        opts, args = getopt.getopt(sys.argv[1:], 'vot:n:q:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-t':
            tenant = arg
        elif opt == '-n':
            name = arg
        elif opt == '-q':
            vlan = arg
        elif opt == '-o':
            only_subnet = True
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not tenant or not name or not vlan:
        logger.error('tenant, network name or vlan not specified')
        sys.exit(1)
    name = f'{vlan:0>4}_{name}'

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    if only_subnet:
        # Getting subnets
        total, subnets = getSubnets(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, bd = name)
        if total > 0:
            for subnet in subnets:
                network = subnet['fvSubnet']['attributes']['ip']
                if not deleteSubnet(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, name = network, bd = name):
                    logging.error(f'failed to delete {network} from bd {name}')
                    sys.exit(1)
        return

    if not deleteEPG(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, name = name, app = tenant):
        logging.error(f'failed to delete EPG {name}')
        sys.exit(1)

    if not deleteBD(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, name = name):
        logging.error(f'failed to delete bridge domain {name}')
        sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
