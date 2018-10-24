#!/usr/bin/env python3
import json, logging, os, requests, socket, sys, time

pwd = os.path.dirname(os.path.realpath(__file__))
eve_url = 'http://127.0.0.1/api/'
eve_username = 'admin'
eve_password = 'eve'
eve_lab_name = 'CI-CD-test.unl'
eve_lab_filename = pwd + '/lab-test.zip'
node_ips = ['192.0.2.11', '192.0.2.12']

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

def isUp(ip):
    try:
        s = socket.socket()
        s.connect((ip, 22))
        s.close()
        return True
    except Exception as err:
        return False

# Logging in to the EVE-NG server
r = requests.post(eve_url + 'auth/login', verify = False, headers = headers_post_json, data = json.dumps(data))
if r.status_code != 200:
    # Login failed
    logging.error('cannot login to EVE-NG server ({})'.format(r.status_code))
    sys.exit(1)
cookies = r.cookies

# Importing the lab
try:
    f = open(eve_lab_filename, 'rb')
except Exception as err:
    logging.error('cannot read lab file')
    logging.error(err)
    sys.exit(1)
r = requests.post(eve_url + 'import', verify = False, headers = headers, cookies = cookies, files = {'path': (None, '/'), 'file': (eve_lab_filename, f)})
if r.status_code != 200:
    logging.error('failed to upload the lab ({})'.format(r.status_code))
    sys.exit(1)

# Get node IDs
r = requests.get(eve_url + 'labs/' + eve_lab_name + '/nodes', verify = False, headers = headers, cookies = cookies)
if r.status_code != 200:
    logging.error('failed to get nodes ({})'.format(r.status_code))
    sys.exit(1)
nodes = r.json()['data']

# Start nodes
for node_id, node in nodes.items():
    r = requests.get(eve_url + 'labs/' + eve_lab_name + '/nodes/' + node_id + '/start', verify = False, headers = headers, cookies = cookies)
    if r.status_code != 200:
        logging.error('failed to start node {} ({})'.format(node_id, r.status_code))
        sys.exit(1)

# Waiting for nodes
timeout = 500
while timeout > 0 and node_ips:
    for node_ip in node_ips:
        if isUp(node_ip):
            node_ips.remove(node_ip)
    time.sleep(1)
    timeout -= 1
for node_ip in node_ips:
    logging.error('node {} is not up'.format(node_ip))
if node_ips:
    sys.exit(1)
