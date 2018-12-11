#!/usr/bin/env python3
'''
    This script adds a new tenant with VRF and application profile, using the
    same name. If the tenant already exists, -f (force) is required, or the
    script fails.

    Examples:
    # cat tenants.txt | while read line; do ./addTenant.py -t $(echo $line | cut -d, -f1) -d "$(echo $line | cut -d, -f2)"; done
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -t STRING  Tenant Name')
    print('  -d STRING  Tenant Description (optional)')
    print('  -f         Force: if exists then overwrite it')
    sys.exit(1)

def main():
    debug = False
    force = False
    name = None
    description = None

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
        opts, args = getopt.getopt(sys.argv[1:], 'vft:d:')
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
            name = arg
        elif opt == '-d':
            description = arg
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not name:
        logger.error('name not specified')
        sys.exit(1)

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    if not force:
        # Need to check if tenant exists
        total, tenants = getTenants(ip = apic_ip, token = token, cookies = cookies, name = name)
        if total > 0:
            # Tenant exists, cannot continue without forcing
            logging.error(f'tenant "{name}" exists, cannot continue without forcing')
            sys.exit(1)

    if not addTenant(ip = apic_ip, token = token, cookies = cookies, name = name, description = description):
        logging.error(f'failed to create tenant {name}')
        sys.exit(1)

    if not addAppProfile(ip = apic_ip, token = token, cookies = cookies, name = name, description = f'Default application profile for tenant {name}'):
        logging.error(f'failed to create application profile {name}')
        sys.exit(1)

    if not addVRF(ip = apic_ip, token = token, cookies = cookies, name = name, description = f'Default unenforced VRF for tenant {name}'):
        logging.error(f'failed to create VRF {name}')
        sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
