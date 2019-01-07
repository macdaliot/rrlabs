#!/usr/bin/env python3
'''
    This script remove one VLAN, associated to a port (single) or to a PolicyGroup (PC/vPC), from an EPG.

    Examples:
    # ./deletePortFromEPG.py -t Tenant -m access -i 1576 -a single -l Leaf102 -p 1/37 -f 101
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -f         force (delete without asking)')
    print('  -t STRING  Tenant')
    print('  -i INTEGER VLAN ID')
    print('  -a STRING  single|pc|vpc')
    print('  -g STRING  Policy Group (mandatory if PC or vPC is used)')
    print('  -l STRING  leaf (mandatory if single port is used)')
    print('  -p STRING  port (i.e. 1/15, mandatory if single port is used)')
    print('  -F INTEGER FEX ID (i.e. 101, optional if single port is used)')
    sys.exit(1)

def main():
    debug = False
    tenant = None
    vlan = None
    port_type = None
    leaf = None
    group = None
    port = None
    fex = None
    epg_name = None
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
    except:
        logger.error('invalid config.yaml file: missing apic_ip, apic_username or apic_password')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vft:i:a:g:l:p:F:')
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
        elif opt == '-i':
            vlan = arg
        elif opt == '-a':
            port_type = arg
        elif opt == '-g':
            group = arg
        elif opt == '-l':
            leaf = arg
        elif opt == '-p':
            port = arg
        elif opt == '-f':
            fex = arg
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not tenant:
        logger.error('tenant not specified')
        sys.exit(1)
    if not vlan:
        logger.error('vlan not specified')
        sys.exit(1)
    if not port_type or port_type not in ['single', 'pc', 'vpc']:
        logger.error('single|pv|vpc not specified or not valid')
        sys.exit(1)
    if port_type in ['pc', 'vpc'] and not group:
        logger.error('port pc/vpc requires policy group')
        sys.exit(1)
    if port_type == 'single' and (not leaf or not port):
        logger.error('port single requires leaf and port')
        sys.exit(1)

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    # Finding the path
    if port_type == 'single':
        path = getPathFromLeafPort(ip = apic_ip, token = token, cookies = cookies, name = leaf, port = port, fex = fex)
        if not path:
            logging.error(f'cannot find path for {leaf}/{fex}/{port}')
            sys.exit(1)
    else:
        path = getPathFromPolicyGroup(ip = apic_ip, token = token, cookies = cookies, name = group)
        if not path:
            logging.error(f'cannot find path for {group}')
            sys.exit(1)

    # Finding EPG
    total, epgs = getEPGs(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, app = tenant)
    if total > 0:
        for epg in epgs:
            if epg['fvAEPg']['attributes']['name'].startswith(f'{vlan:0>4}_'):
                epg_name = epg['fvAEPg']['attributes']['name']
                break
    if not epg_name:
        logging.error(f'cannot find EPG for VLAN {vlan}')
        sys.exit(1)

    # Getting paths from EPG
    total, paths = getPathFromEPG(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, app = tenant, name = epg_name, path = path)
    if total == 1:
        if not force:
            confirm = input(f'Deleting path {path} from EPG {epg_name}. Continue? [no|yes]')
            if confirm != 'yes':
                print('Aborting...')
                sys.exit(0)
        # Deleting the path from the EPG
        if not deletePathFromEPG(ip = apic_ip, token = token, cookies = cookies, tenant = tenant, app = tenant, name = epg_name, path = path):
            logging.error(f'cannot delete path {path} from EPG')

if __name__ == '__main__':
    main()
    sys.exit(0)
