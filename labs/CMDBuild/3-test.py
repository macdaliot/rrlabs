#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170726'

import ipaddress, json, logging, napalm, requests, sys, urllib3

router_username = 'admin'
router_password = 'cisco'

router_name = sys.argv[1:2]
if not router_name:
    logging.error('ERROR: missing device name')
    sys.exit(1)
router_name = router_name[0]

remote_name = sys.argv[2:3]
if not remote_name:
    logging.error('ERROR: missing remote device name')
    sys.exit(1)
remote_name = remote_name[0]

driver = napalm.get_network_driver('ios')
device = driver(hostname = router_name, username = router_username, password = router_password, optional_args = {'port': 22, 'dest_file_system': 'unix:'})
device.open()
output = device.ping(remote_name)
device.close()
print(json.dumps(output))

