#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170726'

import ipaddress, logging, napalm, requests, sys, urllib3
urllib3.disable_warnings()
logging.basicConfig(level = logging.INFO)

router_username = 'admin'
router_password = 'cisco'
cmdbuild_url = 'http://localhost:8080/cmdbuild-2.4.3/services/rest'
cmdbuild_username = 'admin'
cmdbuild_password = 'admin'

router_ip = sys.argv[1:2]
if not router_ip:
    logging.error('ERROR: missing device IP address')
    sys.exit(1)
router_ip = router_ip[0]

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

driver = napalm.get_network_driver('ios')
device = driver(hostname = router_ip, username = router_username, password = router_password, optional_args = {'port': 22, 'dest_file_system': 'unix:'})
device.open()
device_info = device.get_facts()
device_interfaces = device.get_interfaces()
device_ip = device.get_interfaces_ip()
device.close()

logging.info('INFO: checking if the device already exists')
try:
    r = requests.get('{}/v2/cql?filter=%7B{}%7D'.format(cmdbuild_url, requests.utils.requote_uri('CQL: \"from networkdevices where Description CONTAINS \'' + device_info['hostname'] + '\'\"')), headers = headers, verify = False)
    if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
except:
    e = sys.exc_info()
    logging.error('ERROR: {}'.format(e))
    sys.exit(1)
if r.json()['meta']['total'] != 0:
    logging.info('INFO: device {} already present'.format(device_info['hostname']))
    device_id = r.json()['data'][0]['_id']
else:
    # Adding the device
    logging.info('INFO: adding device {}'.format(device_info['hostname']))
    try:
        post_data = {
            'Code': device_info['serial_number'],
            'Description': device_info['hostname'],
            'Vendor': device_info['vendor'],
            'Version': device_info['os_version']
        }
        r = requests.post('{}/v2/classes/networkdevices/cards'.format(cmdbuild_url), json = post_data, headers = headers, verify = False)
        if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
    except:
        e = sys.exc_info()
        logging.error('ERROR: {}'.format(e))
        sys.exit(1)
    device_id = r.json()['data']

interface_id = {}
ip_id = {}
network_id = {}
for interface_name, interface in device_interfaces.items():
    logging.info('INFO: checking if the interface already exists')
    try:
        r = requests.get('{}/v2/cql?filter=%7B{}%7D'.format(cmdbuild_url, requests.utils.requote_uri('CQL: \"from interfaces where Description CONTAINS \'' + device_info['hostname'] + ':' + interface_name + '\'\"')), headers = headers, verify = False)
        if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
    except:
        e = sys.exc_info()
        logging.error('ERROR: {}'.format(e))
        sys.exit(1)
    if r.json()['meta']['total'] != 0:
        logging.info('INFO: interface {}:{} already present'.format(device_info['hostname'], interface_name))
        interface_id[interface_name] = r.json()['data'][0]['_id']
    else:
        # Adding the interface
        logging.info('INFO: adding interface {}'.format(interface_name))
        try:
            post_data = {
                'Code': interface['mac_address'].lower(),
                'Description': '{}:{}'.format(device_info['hostname'], interface_name)
            }
            r = requests.post('{}/v2/classes/interfaces/cards'.format(cmdbuild_url), json = post_data, headers = headers, verify = False)
            if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
        except:
            e = sys.exc_info()
            logging.error('ERROR: {}'.format(e))
            sys.exit(1)
        interface_id[interface_name] = r.json()['data']

        logging.info('INFO: adding relationship between {} and {}'.format(device_info['hostname'], interface_name))
        try:
            post_data = {
                '_sourceType': 'networkdevices',
                '_sourceId': device_id,
                '_destinationType': 'interfaces',
                '_destinationId': r.json()['data']
            }
            q = requests.post('{}/v2/domains/networkdevice2interfaces/relations'.format(cmdbuild_url), json = post_data, headers = headers, verify = False)
            if q.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(q.status_code))
        except:
            e = sys.exc_info()
            logging.error('ERROR: {}'.format(e))
            sys.exit(1)

    if interface_name in device_ip and 'ipv4' in device_ip[interface_name]:
        for ip, attrs in device_ip[interface_name]['ipv4'].items():
            device_interface = ipaddress.IPv4Interface('{}/{}'.format(ip, attrs['prefix_length']))
            logging.info('INFO: checking if the network already exists')
            try:
                r = requests.get('{}/v2/cql?filter=%7B{}%7D'.format(cmdbuild_url, requests.utils.requote_uri('CQL: \"from networks where Description CONTAINS \'' + str(device_interface.network) + '\'\"')), headers = headers, verify = False)
                if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
            except:
                e = sys.exc_info()
                logging.error('ERROR: {}'.format(e))
                sys.exit(1)
            if r.json()['meta']['total'] != 0:
                logging.info('INFO: network {} already present'.format(device_interface.network))
                network_id[str(device_interface.network)] = r.json()['data'][0]['_id']
            else:
                # Adding the network
                logging.info('INFO: adding network {}'.format(device_interface.network))
                try:
                    post_data = {
                        'Description': str(device_interface.network)
                    }
                    r = requests.post('{}/v2/classes/ipv4networks/cards'.format(cmdbuild_url), json = post_data, headers = headers, verify = False)
                    if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
                except:
                    e = sys.exc_info()
                    logging.error('ERROR: {}'.format(e))
                    sys.exit(1)
                network_id[str(device_interface.network)] = r.json()['data']

            logging.info('INFO: checking if the IP already exists')
            try:
                r = requests.get('{}/v2/cql?filter=%7B{}%7D'.format(cmdbuild_url, requests.utils.requote_uri('CQL: \"from ipv4addresses where Description CONTAINS \'' + str(device_interface.ip) + '\'\"')), headers = headers, verify = False)
                if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
            except:
                e = sys.exc_info()
                logging.error('ERROR: {}'.format(e))
                sys.exit(1)
            if r.json()['meta']['total'] != 0:
                logging.info('INFO: IP {} already present'.format(device_interface.ip))
                ip_id[str(device_interface.ip)] = r.json()['data'][0]['_id']
            else:
                # Adding the IP
                logging.info('INFO: adding IP {}'.format(device_interface.ip))
                try:
                    post_data = {
                        'Description': str(device_interface.ip)
                    }
                    r = requests.post('{}/v2/classes/ipv4addresses/cards'.format(cmdbuild_url), json = post_data, headers = headers, verify = False)
                    if r.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(r.status_code))
                except:
                    e = sys.exc_info()
                    logging.error('ERROR: {}'.format(e))
                    sys.exit(1)
                ip_id[str(device_interface.ip)] = r.json()['data']
                logging.info('INFO: adding relationship between {} and {}'.format(str(device_interface.ip), interface_name))
                try:
                    post_data = {
                        '_sourceType': 'interfaces',
                        '_sourceId': interface_id[interface_name],
                        '_destinationType': 'ipv4addresses',
                        '_destinationId': ip_id[str(device_interface.ip)]
                    }
                    q = requests.post('{}/v2/domains/interface2ipv4addresses/relations'.format(cmdbuild_url), json = post_data, headers = headers, verify = False)
                    if q.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(q.status_code))
                except:
                    e = sys.exc_info()
                    logging.error('ERROR: {}'.format(e))
                    sys.exit(1)
                logging.info('INFO: adding relationship between {} and {}'.format(str(device_interface.ip), str(device_interface.network)))
                try:
                    post_data = {
                        '_sourceType': 'ipv4addresses',
                        '_sourceId': ip_id[str(device_interface.ip)],
                        '_destinationType': 'networks',
                        '_destinationId': network_id[str(device_interface.network)]
                    }
                    q = requests.post('{}/v2/domains/ipv4addresstoipv4network/relations'.format(cmdbuild_url), json = post_data, headers = headers, verify = False)
                    if q.status_code != 200: raise Exception('HTTP Error', 'Received HTTP {} code'.format(q.status_code))
                except:
                    e = sys.exc_info()
                    logging.error('ERROR: {}'.format(e))
                    sys.exit(1)

sys.exit(0)

