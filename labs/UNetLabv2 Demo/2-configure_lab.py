#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170526'

import ipaddress, json, logging, napalm, os, requests, subprocess, sys, urllib3
urllib3.disable_warnings()
logging.basicConfig(level = logging.INFO)

node_username = 'admin'
node_password = 'UNetLabv2!'
master_url = 'https://172.16.0.1'
master_key = '?api_key=zqg81ge585t0bt3qe0sjj1idvw7hv7vfgc11dsq6'

if not os.path.isfile('lab.json'):
    logging.error('File lab.json not found, run 1-build_lab.py before')
    sys.exit(1)

# Checking if lab.json is available
try:
    with open('lab.json') as json_data:
        jlab = json.load(json_data)
        json_data.close()
except:
    logging.error('File lab.json not valid')
    sys.exit(1)
lab_id = jlab['id']

# Checking if controller is available
try:
    r = requests.get('{}/'.format(master_url), verify = False)
except:
    logging.error('UNetLabv2 controller is not available')
    sys.exit(1)

r = requests.get('{}/api/v1/labs/{}{}'.format(master_url, lab_id, master_key), verify = False)
if r.status_code != 200:
    logging.error('Cannot get lab "{}"'.format(lab_id))
    sys.exit(1)
data = r.json()
jlab = data['data'][lab_id]

# Writing lab to file for next scripts
with open('lab.json', 'w') as outfile:
    json.dump(jlab, outfile)

# Configuring nodes
for node_id, node in jlab['topology']['nodes'].items():
    logging.info('Configuring node_{} ({})'.format(node['label'], node['name']))
    driver = napalm.get_network_driver('ios')
    device = driver(hostname = node['ip'], username = node_username, password = node_password, optional_args = {'port': 22, 'dest_file_system': 'unix:'})
    device.open()
    config = 'hostname {}\n'.format(node['name'])
    if 'ospf' in node:
        for process_id, process in node['ospf']['process'].items():
            config = config + 'router ospf {}\n'.format(process_id)
            if 'default-passive' in process and process['default-passive'] == True:
                config = config + 'passive-interface default\n'
    for interface_id, interface in node['interfaces'].items():
        config = config + 'interface {}\n'.format(interface['name'])
        if 'description' in interface:
            config = config + 'description {}\n'.format(interface['description'])
        if 'ipv4' in interface:
            ipv4 = ipaddress.IPv4Interface(interface['ipv4'])
            config = config + 'ip address {} {}\n'.format(ipv4.ip, ipv4.netmask)
            config = config + 'no shutdown\n'
        if 'ospf' in interface:
            for process_id, process in interface['ospf']['process'].items():
                config = config + 'interface {}\n'.format(interface['name'])
                config = config + 'ip ospf {} area {}\n'.format(process_id, process['area'])
                config = config + 'router ospf {}\n'.format(process_id)
                if 'passive' in interface['ospf'] and interface['ospf']['passive'] == True:
                    config = config + 'passive-interface {}\n'.format(interface['name'])
                elif 'passive' in interface['ospf'] and interface['ospf']['passive'] == False:
                    config = config + 'no passive-interface {}\n'.format(interface['name'])
    device.load_merge_candidate(config = config)
    diff = device.compare_config()
    device.commit_config()
    device.close()

