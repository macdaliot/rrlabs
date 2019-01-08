#!/usr/bin/env python3
'''
    This script configure a Fex attached to one leaf on one or more ports.

    Examples:
    # ./deleteFex.py -i 101 -l Leaf101
'''

import getopt, logging, sys, yaml
from functions import *

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -v         Be verbose and enable debug')
    print('  -F INT     Fex ID (i.e. 101)')
    print('  -l STRING  Leaf Profile (i.e. Leaf101)')
    print('  -f         force (delete without asking)')
    sys.exit(1)

def main():
    debug = False
    force = False
    id = None
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
    except:
        logger.error('invalid config.yaml file: missing apic_ip, apic_username or apic_password')

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vfF:l:')
    except getopt.GetoptError as err:
        logger.error('exception while parsing options', exc_info = debug)
        usage()
    for opt, arg in opts:
        if opt == '-v':
            debug = True
            logger.setLevel(logging.DEBUG)
        elif opt == '-F':
            id = int(arg)
        elif opt == '-l':
            leaf_profile = arg
        elif opt == '-f':
            force = True
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()

    # Checking options
    if len(sys.argv) == 1:
        usage()
    if not leaf_profile:
        logger.error('leaf not specified')
        sys.exit(1)
    if not id or id < 101 or id > 199:
        logger.error('fex id not specified or not between 101 and 199')
        sys.exit(1)
    name = f'Fex{id}'
    fex_profile_name = f'FEX_{leaf_profile}:{name}'
    leaf_profile_name = f'{leaf_profile}:{name}'

    # Login
    token, cookies = login(username = apic_username, password = apic_password, ip = apic_ip)
    if not token or not cookies:
        logging.error('authentication failed')
        sys.exit(1)

    # Check if FEX profile exists
    total, unused = getFexProfile(ip = apic_ip, token = token, cookies = cookies, name = fex_profile_name)
    if total is 0:
        logging.error(f'Fex profile {fex_profile_name} does not exist')
        sys.exit(1)

    # Check if FEX Profile is empty
    total, unused = getInterfaceSelectorBlocks(ip = apic_ip, token = token, cookies = cookies, profile = fex_profile_name, fex = True)
    if total is not 0:
        logging.error(f'FEX profile {fex_profile_name} is used')
        sys.exit(1)

    # Unbind the interface profile from the switch profile
    if not force:
        confirm = input(f'Unbinding {leaf_profile_name} from {leaf_profile}. Continue? [no|yes]')
        if confirm != 'yes':
            print('Aborting...')
            sys.exit(0)
    if not unbindSwitchProfileFromInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile, interface_profile = leaf_profile_name):
        logging.error('failed to unbind interface profile from leaf')
        sys.exit(1)

    # Delete the leaf interface profile
    if not force:
        confirm = input(f'Deleting interface profile {leaf_profile_name}. Continue? [no|yes]')
        if confirm != 'yes':
            print('Aborting...')
            sys.exit(0)
    if not deleteInterfaceProfile(ip = apic_ip, token = token, cookies = cookies, name = leaf_profile_name):
        logging.error('failed to delete leaf interface profile')
        sys.exit(1)

    # Delete Fex Profile
    if not force:
        confirm = input(f'Deleting FEX profile {fex_profile_name}. Continue? [no|yes]')
        if confirm != 'yes':
            print('Aborting...')
            sys.exit(0)
    if not deleteFexProfile(ip = apic_ip, token = token, cookies = cookies, name = fex_profile_name):
        logging.error(f'failed to delete {fex_profile_name}')
        sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)
