#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170726'

import ipaddress, json, logging, napalm, requests, sys, urllib3
urllib3.disable_warnings()
logging.basicConfig(level = logging.INFO)

router_username = 'admin'
router_password = 'cisco'
cmdbuild_url = 'http://localhost:8080/cmdbuild-2.4.3/services/rest'
cmdbuild_username = 'admin'
cmdbuild_password = 'admin'

router_name = sys.argv[1:2]
if not router_name:
    logging.error('ERROR: missing device name')
    sys.exit(1)
router_name = router_name[0]

try:
    post_data = {
        'username': cmdbuild_username,
        'password': cmdbuild_password
    }
    r = requests.post('{}/v1/sessions'.format(cmdbuild_url), json = post_data, verify = False)
    if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
except:
    e = sys.exc_info()
    logging.error('ERROR: {}'.format(e))
    sys.exit(1)

headers = {'CMDBuild-Authorization': r.json()['data']['_id']}

logging.info('INFO: looking for the device')
try:
    r = requests.get('{}/v2/cql?filter=%7B{}%7D'.format(cmdbuild_url, requests.utils.requote_uri('CQL: \"from networkdevices where Description CONTAINS \'' + router_name + '\'\"')), headers = headers, verify = False)
    if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
except:
    e = sys.exc_info()
    logging.error('ERROR: {}'.format(e))
    sys.exit(1)
if r.json()['meta']['total'] != 0:
    logging.info('INFO: device {} found'.format(router_name))
    device_id = r.json()['data'][0]['_id']

logging.info('INFO: looking for the interfaces')
interfaces = []
try:
    r = requests.get('{}/v2/domains/networkdevice2interfaces/relations'.format(cmdbuild_url), headers = headers, verify = False)
    if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
except:
    e = sys.exc_info()
    logging.error('ERROR: {}'.format(e))
    sys.exit(1)
if r.json()['meta']['total'] != 0:
    for relationship in r.json()['data']:
        if relationship['_sourceId'] == device_id:
            interface_id = relationship['_destinationId']
            try:
                r = requests.get('{}/v2/classes/interfaces/cards/{}'.format(cmdbuild_url, interface_id), headers = headers, verify = False)
                if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
            except:
                e = sys.exc_info()
                logging.error('ERROR: {}'.format(e))
                sys.exit(1)
            interface = {
                'name': r.json()['data']['Description'],
                'ipv4': []
            }

            logging.info('INFO: looking for the IP addresses')
            try:
                r = requests.get('{}/v2/domains/interface2ipv4addresses/relations'.format(cmdbuild_url), headers = headers, verify = False)
                if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
            except:
                e = sys.exc_info()
                logging.error('ERROR: {}'.format(e))
                sys.exit(1)
            for relationship in r.json()['data']:
                if relationship['_sourceId'] == interface_id:
                    ipv4_id = relationship['_destinationId']
                    try:
                        r = requests.get('{}/v2/classes/ipv4addresses/cards/{}'.format(cmdbuild_url, ipv4_id), headers = headers, verify = False)
                        if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
                    except:
                        e = sys.exc_info()
                        logging.error('ERROR: {}'.format(e))
                        sys.exit(1)
                    ipv4_address = r.json()['data']['Description']
                    ipv4_address_id = r.json()['data']['_id']

                    logging.info('INFO: looking for the network')
                    try:
                        r = requests.get('{}/v2/domains/ipv4addresstoipv4network/relations'.format(cmdbuild_url), headers = headers, verify = False)
                        if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
                    except:
                        e = sys.exc_info()
                        logging.error('ERROR: {}'.format(e))
                        sys.exit(1)
                    for relationship in r.json()['data']:
                        if relationship['_sourceId'] == ipv4_address_id:
                            network = relationship['_destinationDescription']
                            break

                    network = ipaddress.ip_network(network)
                    interface['ipv4'].append('{}/{}'.format(ipv4_address, network.prefixlen))
            interfaces.append(interface)

# Got data from CMDB
config = ''
router_ip = None
for interface in interfaces:
    config = config + 'interface {}\n'.format(interface['name'].split(':')[1])
    if interface['ipv4']:
        first = True
        for ipv4 in interface['ipv4']:
            ipv4address = ipaddress.ip_interface(ipv4)
            if not router_ip:
                router_ip = str(ipv4address.ip)
            if first:
                config = config + 'ip address {} {}\n'.format(ipv4address.ip, ipv4address.netmask)
            else:
                config = config + 'ip address {} {} secondary\n'.format(ipv4address.ip, ipv4address.netmask)
            first = False
        config = config + 'no shutdown\n'
    else:
        config = config + 'shutdown\n'
config = config + 'end\n'
driver = napalm.get_network_driver('ios')
device = driver(hostname = router_ip, username = router_username, password = router_password, optional_args = {'port': 22, 'dest_file_system': 'unix:'})
device.open()
device.load_merge_candidate(config = config)
diff = device.compare_config()
device.commit_config()
device.close()

