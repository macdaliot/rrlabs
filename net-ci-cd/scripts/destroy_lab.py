#!/usr/bin/env python3
import json, logging, requests, sys

eve_url = 'http://192.168.102.130/api/'
eve_username = 'admin'
eve_password = 'eve'
eve_lab_name = 'CI-CD-test.unl'
eve_lab_filename = 'lab-test.zip'
node_ids = [1, 2]
node_ips = ['192.168.102.142', '192.168.102.145']

headers = {
    'Accept': 'application/json;',
}
headers_post_json = {
    'Accept': 'application/json;',
    'Content-Type': 'application/json'
}
data = {
    'username': eve_username,
    'password': eve_password,
    'html5': -1
}

# Logging in to the EVE-NG server
r = requests.post(eve_url + 'auth/login', verify = False, headers = headers_post_json, data = json.dumps(data))
if r.status_code != 200:
    # Login failed
    logging.error('cannot login to EVE-NG server ({})'.format(r.status_code))
    sys.exit(1)
cookies = r.cookies

# Checking if lab exists
r = requests.get(eve_url + 'labs/' + eve_lab_name + '/nodes', verify = False, headers = headers, cookies = cookies)
if r.status_code == 404:
    # Lab does not exist, nothing to do
    sys.exit(0)
elif r.status_code != 200:
    # Failed to check exzisting lab
    logging.error('unexpected result when checking if lab exists ({})'.format(r.status_code))
    sys.exit(1)

# Get node IDs
r = requests.get(eve_url + 'labs/' + eve_lab_name + '/nodes', verify = False, headers = headers, cookies = cookies)
if r.status_code != 200:
    logging.error('failed to get nodes ({})'.format(r.status_code))
    sys.exit(1)
nodes = r.json()['data']

# Stop nodes
for node_id, node in nodes.items():
    r = requests.get(eve_url + 'labs/' + eve_lab_name + '/nodes/' + node_id + '/stop', verify = False, headers = headers, cookies = cookies)
    if r.status_code != 200:
        logging.error('failed to stop node {} ({})'.format(node_id, r.status_code))
        sys.exit(1)

# Deleting existing lab
r = requests.delete(eve_url + 'labs/' + eve_lab_name, verify = False, headers = headers, cookies = cookies)
if r.status_code != 200:
    # Deletion failed
    logging.error('failed to delete existing lab ({})'.format(r.status_code))
    sys.exit(1)
