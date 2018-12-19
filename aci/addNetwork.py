#!/usr/bin/env python3
'''
    This script adds a new network in terms of Bridge Domain and EPG. Options
    are set for a brownfield installation. If the Bridge Domain and/or the EPG already exist, -f (force) is required, or the script fails.
    The MAC address is optional and can be in the Cisco ACI range (starting with 00:22:BD) or in the HSRP range (00:00:0C).

    Examples:
    # ./addNetwork.py -t Tenant -n Prod_Network -q 1110 -d "Network for production" -m 00:00:0c:aa:bb:cc -s 192.168.1.1/24 -v -f
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -t STRING  Tenant Name')
    print('  -n STRING  Network Name')
    print('  -q INT     VLAN ID (802.1Q)')
    print('  -d STRING  Network Description (optional)')
    print('  -m STRING  MAC address (i.e. 00:22:BD:aa:bb:cc, optional)')
    print('  -s STRING  Subnet (i.e. 192.168.0.1/24, mandatory with -o)')
    print('  -o         Create subnet only (optional)')
    print('  -f         Force: if exists then overwrite it')
    sys.exit(1)

def main():
    debug = False
    force = False
    tenant = None
    name = None
    description = None
    mac = None
    subnet = None
    vlan = None
    subnet_only = False
    bridge_exists = False
    epg_exists = False
    subnet_exists = False
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
        domain_l2 = config['domain_l2']
    except:
        logger.error('invalid config.yaml file: missing apic_ip, apic_username, apic_password or domain_l2')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'voft:n:d:m:s:q:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-f':
            force = True
        elif opt == '-t':
            tenant = arg
        elif opt == '-n':
            name = arg
        elif opt == '-q':
            vlan = arg
        elif opt == '-d':
            description = arg
        elif opt == '-m':
            mac = arg
        elif opt == '-s':
            subnet = arg
        elif opt == '-o':
            subnet_only = True
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

    if not force:
        # Need to check if bridge domain exists
        total, bds = getBDs(ip = apic_ip, token = token, cookies = cookies, name = name, tenant = tenant)
        if total > 0:
            bridge_exists = True

            # Need to check if subnet exists
            total, subnets = getSubnets(ip = apic_ip, token = token, cookies = cookies, bd = name, tenant = tenant, name = subnet)
            if total > 0:
                # Subnet exists, cannot continue without forcing
                subnet_exists = True

        # Need to check if EPG exists
        total, epgs = getEPGs(ip = apic_ip, token = token, cookies = cookies, name = name, tenant = tenant, app = tenant)
        if total > 0:
            epg_exists = True

    if subnet:
        # Binding the BD to the L3Out (mandatory to avoid blackhole)
        if not bindBDtoL3Out(ip = apic_ip, token = token, cookies = cookies, name = name, tenant = tenant, l3out = f'L3OUT_{tenant}'):
            logger.error(f'failed to bind L3Oout to BD {bd_name}')
            sys.exit(1)

    if subnet_only:
        # Working on subnet only
        if subnet:
            if subnet_exists:
                logging.error(f'Subnet "{subnet}" exists inside parent bridge domain ”{name}", cannot continue without forcing')
                sys.exit(1)
            if not bridge_exists:
                logging.error(f'Cannot create subnet "{subnet}" if parent bridge domain "{name}" is missing')
                sys.exit(1)
            if not addSubnet(ip = apic_ip, token = token, cookies = cookies, bd = name, description = description, tenant = tenant, name = subnet):
                logging.error(f'failed to create subnet {subnet}')
                sys.exit(1)
        return

    if bridge_exists:
        # Bridge domain exists, cannot continue without forcing
        logging.error(f'bridge domain "{name}" exists, cannot continue without forcing')
    else:
        if not addBD(ip = apic_ip, token = token, cookies = cookies, name = name, description = description, tenant = tenant, mac = mac, subnet = subnet, vrf = tenant):
            logging.error(f'failed to create bridge domain {name}')
            sys.exit(1)

    if epg_exists:
        # EPG exists, cannot continue without forcing
        logging.error(f'EPG "{name}" exists, cannot continue without forcing')
    else:
        if not addEPG(ip = apic_ip, token = token, cookies = cookies, name = name, description = description, tenant = tenant, bd = name, app = tenant, domain = domain_l2):
            logging.error(f'failed to create EPG {name}')
            sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
