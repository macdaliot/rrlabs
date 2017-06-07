#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170526'

import json, logging, os, subprocess, sys, urllib3

#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170526'

username = 'admin'
password = 'UNetLabv2!'

import ipaddress, logging, napalm, sys, os

logging.basicConfig(level = logging.INFO)

if not os.path.isfile('lab.json'):
    logging.error('File lab.json not found, run 1-build_lab.py before')
    sys.exit(1)

try:
    with open('lab.json') as json_data:
        jlab = json.load(json_data)
        json_data.close()
except:
    logging.error('File lab.json not valid')
    sys.exit(1)

for node_id, node in jlab['topology']['nodes'].items():
    logging.info('Configuring node_{} ({})'.format(node['label'], node['name']))
    driver = napalm.get_network_driver('ios')
    device = driver(hostname = node['docker_ip'], username = username, password = password, optional_args = {'port': 22, 'dest_file_system': 'unix:'})
    device.open()
    config = 'hostname {}\n'.format(node['name'])
    for interface_id, interface in node['interfaces'].items():
        config = config + 'interface {}\n'.format(interface['name'])
        if 'description' in interface:
            config = config + 'description {}\n'.format(interface['description'])
        if 'ipv4' in interface:
            ipv4 = ipaddress.IPv4Interface(interface['ipv4'])
            config = config + 'ip address {} {}\n'.format(ipv4.ip, ipv4.netmask)
            config = config + 'no shutdown\n'
    device.load_merge_candidate(config = config)
    diff = device.compare_config()
    device.commit_config()
    device.close()

