#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170526'

import ipaddress, json, logging, os, requests, subprocess, sys, urllib3
urllib3.disable_warnings()
logging.basicConfig(level = logging.INFO)

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
    print('node_{}: {} {}'.format(node['label'], node['name'], node['ip']))

