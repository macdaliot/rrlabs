#!/usr/bin/env python3
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170526'

master_url = 'http://127.0.0.1:5000'
master_key = '?api_key=zqg81ge585t0bt3qe0sjj1idvw7hv7vfgc11dsq6'
docker_url = 'http://127.0.0.1:4243'

import json, logging, sys, urllib3

headers = {'Content-Type': 'application/json'}
image = 'L3-ADVENTERPRISEK9-M-15.5-2T'
jlab = {
    'name': 'UNetLabv2 Demo',
    'repository': 'local',
    'version': 1,
    'author': 'Andrea Dainese <andrea.dainese@gmail.com>',
    'topology': {
        'nodes': {
            '0': {
                'name': 'Client',
                'type': 'iol',
                'image': image,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '0': {
                        'name': 'e0/1',
                        'description': 'To ISP A',
                        'connection': 0,
                        'ipv4': '192.168.0.1/24'
                    },
                    '1': {
                        'name': 'e0/2',
                        'description': 'To ISP B',
                        'connection': 1,
                        'ipv4': '192.168.1.1/24'
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '192.168.255.0/32'
                    }
                }
            },
            '1': {
                'name': 'ISPA',
                'type': 'iol',
                'image': image,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '1': {
                        'name': 'e0/1',
                        'description': 'To Client',
                        'connection': 0,
                        'ipv4': '192.168.0.254/24'
                    },
                    '2': {
                        'name': 'e0/2',
                        'description': 'To Internet',
                        'connection': 2,
                        'ipv4': '192.168.2.1/24'
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '192.168.255.1/32'
                    }
                }
            },
            '2': {
                'name': 'ISPB',
                'type': 'iol',
                'image': image,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '1': {
                        'name': 'e0/1',
                        'description': 'To Client',
                        'connection': 1,
                        'ipv4': '192.168.1.254/24'
                    },
                    '2': {
                        'name': 'e0/2',
                        'description': 'To Internet',
                        'connection': 3,
                        'ipv4': '192.168.3.254/24'
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '192.168.255.2/32'
                    }
                }
            },
            '3': {
                'name': 'Internet',
                'type': 'iol',
                'image': image,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '1': {
                        'name': 'e0/1',
                        'description': 'To ISPA',
                        'connection': 2,
                        'ipv4': '192.168.2.254/24'
                    },
                    '2': {
                        'name': 'e0/2',
                        'description': 'To ISPB',
                        'connection': 3,
                        'ipv4': '192.168.3.254/24'
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '1.1.1.1/32'
                    }
                }
            }
        },
        'connections': {
            '0': {
                'type': 'ethernet',
                'shutdown': False
            },
            '1': {
                'type': 'ethernet',
                'shutdown': False
            },
            '2': {
                'type': 'ethernet',
                'shutdown': False
            },
            '3': {
                'type': 'ethernet',
                'shutdown': False
            }
        }
    }
}

http = urllib3.PoolManager()

# Checking if controller is available
try:
    r = http.request('GET', '{}/'.format(master_url))
except:
    logging.error('UNetLabv2 master controller is not available. Please start it using run_controller.py runserver --host=0.0.0.0')
    sys.exit(1)

# Checking if Docker is available
try:
    r = http.request('GET', '{}/'.format(docker_url))
except:
    logging.error('Docker Remote API server is not available. Please start it on port 4243')
    sys.exit(1)

# Checking controller authentication
r = http.request('GET', '{}/api/v1/auth{}'.format(master_url, master_key))
if r.status != 200:
    logging.error('Cannot authenticate to UNetLabv2 master controller')
    sys.exit(1)

# Checking Docker API
r = http.request('GET', '{}/containers/json'.format(docker_url))
if r.status != 200:
    logging.error('Cannot list Docker nodes, something wrong with API')
    sys.exit(1)

# Checking Docker image
r = http.request('GET', '{}/images/dainok/node-iol:{}/json'.format(docker_url, image))
if r.status != 200:
    logging.error('Cannot list Docker image node-iol:{}, please pull it'.format(image))
    sys.exit(1)

# Adding the lab
r = http.request('POST', '{}/api/v1/labs{}&commit=true'.format(master_url, master_key), body = json.dumps(jlab).encode('utf-8'), headers = headers)
data = json.loads(r.data.decode('utf-8'))
if r.status != 200:
    logging.error('Cannot create lab ({})'.format(data['message']))
    sys.exit(1)
jlab = data['data']

# Starting nodes
for node_id, node in jlab['topology']['nodes'].items():
    print(node_id)
    print(node['name'])
    print(node['label'])
    print('docker run --name node_{} --env CONTROLLER=172.17.0.1 --env LABEL={} dainok/node-iol:{}'.format(node['label'], node['label'], image))


