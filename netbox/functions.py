#!/usr/bin/env python3
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://www.gnu.org/licenses/gpl.html'
__revision__ = '20170329'

import getopt, json, logging, os, sys
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

ignore_snmp_interfaces = [
    'Null0',
    'VoIP-Null0'
]

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('  -i STRING  inventory file')
    print('  -d         enable debug')
    sys.exit(1)

def checkOpts():
    inventory_file = None
    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'di:')
    except getopt.GetoptError as err:
        logger.error('cannot parse options', exc_info = True)
        usage()

    for opt, arg in opts:
        if opt == '-d':
            logger.setLevel(logging.DEBUG)
        elif opt == '-i':
            inventory_file = arg
            working_dir = '{}/working/{}/devices'.format(os.path.dirname(os.path.abspath(arg)), os.environ.get('NETDOC_FOLDER', 'default'))
        else:
            logger.error('unhandled option ({})'.format(opt))
            usage()
            sys.exit(1)

    # Checking options and environment
    if not inventory_file:
        logger.error('inventory file not specified')
        usage()
    if not os.path.isfile(inventory_file):
        logger.error('inventory file "{}" does not exist'.format(inventory_file))
        sys.exit(1)

    # Loading Ansible inventory
    ansible_loader = DataLoader()
    try:
        ansible_inventory = InventoryManager(loader = ansible_loader, sources = inventory_file)
    except Exception as err:
        logger.error('cannot read inventory file "{}"'.format(inventory_file), exc_info = True)
    variable_manager = VariableManager(loader = ansible_loader, inventory = ansible_inventory)
    return ansible_inventory.get_hosts(), working_dir

def writeDeviceInfo(device_info, path):
    for key, value in device_info.items():
        try:
            os.makedirs(path, exist_ok = True)
        except Exception as err:
            logger.error('cannot create directory "{}"'.format(path), exc_info = True)
        try:
            output = open('{}/{}.json'.format(path, key), 'w+')
            output.write(json.dumps(value, sort_keys=True, indent=4, separators=(',', ': ')))
            output.close()
        except Exception as err:
            logger.error('cannot write "{}/{}.json"'.format(path, key), exc_info = True)
    return True
