#!/usr/bin/env python3.5
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170526'

import json, logging, os, requests, subprocess, sys, urllib3
urllib3.disable_warnings()

master_url = 'https://172.16.0.1'
master_key = '?api_key=zqg81ge585t0bt3qe0sjj1idvw7hv7vfgc11dsq6'

logging.basicConfig(level = logging.INFO)
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
                'iol_id': 1,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'ospf': {
                    'process': {
                        '1': {
                            'default-passive': True
                        }
                    }
                },
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '16': {
                        'name': 'e0/1',
                        'description': 'To ISP A',
                        'connection': 0,
                        'ipv4': '192.168.0.1/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '32': {
                        'name': 'e0/2',
                        'description': 'To ISP B',
                        'connection': 1,
                        'ipv4': '192.168.1.1/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '192.168.255.0/32',
                        'ospf': {
                            'passive': True,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    }
                }
            },
            '1': {
                'name': 'ISPA',
                'type': 'iol',
                'image': image,
                'iol_id': 2,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'ospf': {
                    'process': {
                        '1': {
                            'default-passive': True
                        }
                    }
                },
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '16': {
                        'name': 'e0/1',
                        'description': 'To Client',
                        'connection': 0,
                        'ipv4': '192.168.0.254/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '32': {
                        'name': 'e0/2',
                        'description': 'To Internet',
                        'connection': 2,
                        'ipv4': '192.168.2.1/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '192.168.255.1/32',
                        'ospf': {
                            'passive': True,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    }
                }
            },
            '2': {
                'name': 'ISPB',
                'type': 'iol',
                'image': image,
                'iol_id': 3,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'ospf': {
                    'process': {
                        '1': {
                            'default-passive': True
                        }
                    }
                },
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '16': {
                        'name': 'e0/1',
                        'description': 'To Client',
                        'connection': 1,
                        'ipv4': '192.168.1.254/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '32': {
                        'name': 'e0/2',
                        'description': 'To Internet',
                        'connection': 3,
                        'ipv4': '192.168.3.1/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '192.168.255.2/32',
                        'ospf': {
                            'passive': True,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    }
                }
            },
            '3': {
                'name': 'Internet',
                'type': 'iol',
                'image': image,
                'iol_id': 4,
                'ethernet': 3,
                'serial': 0,
                'ram': 1024,
                'ospf': {
                    'process': {
                        '1': {
                            'default-passive': True
                        }
                    }
                },
                'interfaces': {
                    '0': {
                        'name': 'e0/0',
                        'description': 'Management',
                        'management': True
                    },
                    '16': {
                        'name': 'e0/1',
                        'description': 'To ISPA',
                        'connection': 2,
                        'ipv4': '192.168.2.254/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '32': {
                        'name': 'e0/2',
                        'description': 'To ISPB',
                        'connection': 3,
                        'ipv4': '192.168.3.254/24',
                        'ospf': {
                            'passive': False,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
                    },
                    '100': {
                        'name': 'lo0',
                        'description': 'Loopback',
                        'ipv4': '1.1.1.1/32',
                        'ospf': {
                            'passive': True,
                            'process': {
                                '1': {
                                    'area': 0
                                }
                            }
                        }
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

# Checking if controller is available
try:
    r = requests.get('{}/'.format(master_url), verify = False)
except:
    logging.error('UNetLabv2 controller is not available')
    sys.exit(1)

# Checking controller authentication
r = requests.get('{}/api/v1/auth{}'.format(master_url, master_key), verify = False)
if r.status_code != 200:
    logging.error('Cannot authenticate to UNetLabv2 master controller')
    sys.exit(1)

# Adding the lab
r = requests.post('{}/api/v1/labs{}&commit=true'.format(master_url, master_key), json = jlab, verify = False)
data = r.json()
if r.status_code != 200:
    logging.error('Cannot create lab ({})'.format(data['message']))
    sys.exit(1)
jlab = data['data']

# Starting nodes
for node_id, node in jlab['topology']['nodes'].items():
    r = requests.get('{}/api/v1/nodes/{}/start{}'.format(master_url, node['label'], master_key), verify = False)
    if r.status_code != 200:
        logging.error('Cannot start node "{}" (label "{}")'.format(node['name'], node['label']))
        sys.exit(1)

# Writing lab to file for next scripts
with open('lab.json', 'w') as outfile:
    json.dump(jlab, outfile)

