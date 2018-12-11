#!/usr/bin/env python3
import json, logging, random, requests, secrets, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
    APIC
'''

def login(ip = None, username = None, password = None):
    if not ip or not username or not password:
        logging.error('missing ip, username or password')
        return False, False

    url = f'https://{ip}/api/aaaLogin.json?gui-token-request=yes'
    payload = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }

    r = requests.post(url, verify = False, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        token = response['imdata'][0]['aaaLogin']['attributes']['urlToken']
        return token, cookies
    else:
        logging.error(f'authentication failed with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Fabric
'''

def getPathFromLeafPort(ip = None, token = None, cookies = None, name = None, port = None, fex = None):
    if not ip or not token or not cookies or not name or not port:
        logging.error('missing ip, token, cookies, name or port')
        return False
    leaf_id = None
    leaf_pod = None

    # Finding leaf ID and POD
    url = f'https://{ip}/api/node/class/topSystem.json?query-target-filter=eq(topSystem.role,"leaf")&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        for leaf in response['imdata']:
            leaf_name = leaf['topSystem']['attributes']['name']
            if name == leaf_name:
                # Found the Leaf
                leaf_id = leaf['topSystem']['attributes']['id']
                leaf_pod = leaf['topSystem']['attributes']['podId']
    else:
        logging.error(f'failed to get path with code {response_code}')
        logging.debug(response_text)
        return False

    if not leaf_id or not leaf_pod:
        logging.error(f'cannot find leaf {name}')
        return False

    # Finding path for the leaf
    if fex:
        url = f'https://{ip}/api/node/class/fabricPathEp.json?query-target-filter=and(eq(fabricPathEp.lagT,"not-aggregated"),eq(fabricPathEp.name,"eth{port}"),wcard(fabricPathEp.dn,"^topology/pod-{leaf_pod}/paths-{leaf_id}/extpaths-{fex}/pathep"))&challenge={token}'
    else:
        url = f'https://{ip}/api/node/class/fabricPathEp.json?query-target-filter=and(eq(fabricPathEp.lagT,"not-aggregated"),eq(fabricPathEp.name,"eth{port}"),wcard(fabricPathEp.dn,"^topology/pod-{leaf_pod}/paths-{leaf_id}/pathep"))&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    response = r.json()
    if response_code == 200:
        response = r.json()
        total = int(response['totalCount'])
        if total == 1:
            return response['imdata'][0]['fabricPathEp']['attributes']['dn']
        elif total > 1:
            logging.debug('found multiple path')
        else:
            logging.debug('path not found')
        return False
    else:
        logging.error(f'failed to find path with code {response_code}')
        logging.debug(response_text)
        return False

def getPathFromPolicyGroup(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False

    url = f'https://{ip}/api/node/class/fabricPathEp.json?query-target-filter=and(eq(fabricPathEp.lagT,"node"),wcard(fabricPathEp.dn,"^topology/pod-[\d]*/protpaths-"))&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        for path in response['imdata']:
            path_id = path['fabricPathEp']['attributes']['dn']
            path_name = path['fabricPathEp']['attributes']['name']
            if name == path_name:
                # Found the Policy Group
                return path_id
        return False
    else:
        logging.error(f'failed to find path with code {response_code}')
        logging.debug(response_text)
        return False

'''
    Common policies
'''

def addPolicies(ip = None, token = None, cookies = None, aep = None):
    if not ip or not token or not cookies or not aep:
        logging.error('missing ip, token, cookies or aep')
        return False

    policies = {
        "IGMP_Snoop_Off": {
    		"igmpSnoopPol": {
    			"attributes": {
    				"adminSt": "disabled",
    				"descr": "Disable IGMP Snooping.",
    				"dn": "uni/tn-common/snPol-IGMP_Snoop_Off",
    				"lastMbrIntvl": "1",
    				"queryIntvl": "125",
    				"rspIntvl": "10",
    				"startQueryCnt": "2",
    				"startQueryIntvl": "31"
    			}
    		}
        },
        "IGMP_Snoop_On": {
    		"igmpSnoopPol": {
    			"attributes": {
    				"adminSt": "enabled",
    				"descr": "Enable IGMP Snooping.",
    				"dn": "uni/tn-common/snPol-IGMP_Snoop_On",
    				"lastMbrIntvl": "1",
    				"queryIntvl": "125",
    				"rspIntvl": "10",
    				"startQueryCnt": "2",
    				"startQueryIntvl": "31"
    			}
    		}
        },
    	"CDP_On": {
    		"cdpIfPol": {
    			"attributes": {
    				"adminSt": "enabled",
    				"descr": "Enable CDP protocol.",
    				"dn": "uni/infra/cdpIfP-CDP_On"
    			}
    		}
    	},
    	"CDP_Off": {
    		"cdpIfPol": {
    			"attributes": {
    				"adminSt": "disabled",
    				"descr": "Disable CDP protocol.",
    				"dn": "uni/infra/cdpIfP-CDP_Off"
    			}
    		}
    	},
    	"LLDP_On": {
    		"lldpIfPol": {
    			"attributes": {
    				"adminRxSt": "enabled",
    				"adminTxSt": "enabled",
    				"descr": "Enable LLDP protocol.",
    				"dn": "uni/infra/lldpIfP-LLDP_On"
    			}
    		}
    	},
    	"LLDP_Off": {
    		"lldpIfPol": {
    			"attributes": {
    				"adminRxSt": "disabled",
    				"adminTxSt": "disabled",
    				"descr": "Disable LLDP protocol.",
    				"dn": "uni/infra/lldpIfP-LLDP_Off"
    			}
    		}
    	},
    	"LACP_Active": {
    		"lacpLagPol": {
    			"attributes": {
    				"ctrl": "fast-sel-hot-stdby,graceful-conv,susp-individual",
    				"descr": "Port-Channel with LACP in active mode.",
    				"dn": "uni/infra/lacplagp-LACP_Active",
    				"maxLinks": "16",
    				"minLinks": "1",
    				"mode": "active"
    			}
    		}
    	},
    	"LACP_No_Suspend": {
    		"lacpLagPol": {
    			"attributes": {
    				"ctrl": "fast-sel-hot-stdby,graceful-conv",
    				"descr": "Port-Channel with LACP in active mode. Individual interfaces are not suspended.",
    				"dn": "uni/infra/lacplagp-LACP_No_Suspend",
    				"maxLinks": "16",
    				"minLinks": "1",
    				"mode": "off"
    			}
    		}
    	},
    	"Static": {
    		"lacpLagPol": {
    			"attributes": {
    				"ctrl": "fast-sel-hot-stdby,graceful-conv,susp-individual",
    				"descr": "Static Port-Channel.",
    				"dn": "uni/infra/lacplagp-Static",
    				"maxLinks": "16",
    				"minLinks": "1",
    				"mode": "off"
    			}
    		}
    	},
    	"BPDU_Forward": {
    		"stpIfPol": {
    			"attributes": {
    				"descr": "Forward received BPDUs.",
    				"dn": "uni/infra/ifPol-BPDU_Forward"
    			}
    		}
    	},
    	"BPDU_Guard": {
    		"stpIfPol": {
    			"attributes": {
    				"ctrl": "bpdu-guard",
    				"descr": "Shutdown if receiving BPDU.",
    				"dn": "uni/infra/ifPol-BPDU_Guard"
    			}
    		}
    	},
    	"BPDU_Filter": {
    		"stpIfPol": {
    			"attributes": {
    				"ctrl": "bpdu-filter",
    				"descr": "Filter incoming BPDU.",
    				"dn": "uni/infra/ifPol-BPDU_Filter"
    			}
    		}
    	},
        "SinglePort_Device": {
        	"infraAccPortGrp": {
        		"attributes": {
        			"descr": "Policy for single-homed or multi-homed active-backup network devices which do not speak STP, like routers.",
        			"dn": "uni/infra/funcprof/accportgrp-SinglePort_Device",
        		},
        		"children": [{
        				"infraRsStpIfPol": {
        					"attributes": {
        						"tnStpIfPolName": "BPDU_Guard"
        					}
        				}
        			},
        			{
        				"infraRsCdpIfPol": {
        					"attributes": {
        						"tnCdpIfPolName": "CDP_On"
        					}
        				}
        			},
        			{
        				"infraRsLldpIfPol": {
        					"attributes": {
        						"tnLldpIfPolName": "LLDP_On"
        					}
        				}
        			},
                    {
                    	"infraRsAttEntP": {
                    		"attributes": {
                    			"annotation": "",
                    			"tDn": f"uni/infra/attentp-{aep}"
                    		}
                    	}
                    }
        		]
        	}
        },
        "SinglePort_Server": {
        	"infraAccPortGrp": {
        		"attributes": {
        			"descr": "Policy for single-homed or multi-homed active-backup servers.",
        			"dn": "uni/infra/funcprof/accportgrp-SinglePort_Server",
        		},
        		"children": [{
        				"infraRsStpIfPol": {
        					"attributes": {
        						"tnStpIfPolName": "BPDU_Guard"
        					}
        				}
        			},
        			{
        				"infraRsCdpIfPol": {
        					"attributes": {
        						"tnCdpIfPolName": "CDP_Off"
        					}
        				}
        			},
        			{
        				"infraRsLldpIfPol": {
        					"attributes": {
        						"tnLldpIfPolName": "LLDP_Off"
        					}
        				}
        			},
                    {
                    	"infraRsAttEntP": {
                    		"attributes": {
                    			"annotation": "",
                    			"tDn": f"uni/infra/attentp-{aep}"
                    		}
                    	}
                    }
        		]
        	}
        },
        "SinglePort_Switch": {
        	"infraAccPortGrp": {
        		"attributes": {
        			"descr": "Policy for single-homed or multi-home active-backup network devices which speak STP, like switches.",
        			"dn": "uni/infra/funcprof/accportgrp-SinglePort_Switch",
        		},
        		"children": [{
        				"infraRsStpIfPol": {
        					"attributes": {
        						"tnStpIfPolName": "BPDU_Forward"
        					}
        				}
        			},
        			{
        				"infraRsCdpIfPol": {
        					"attributes": {
        						"tnCdpIfPolName": "CDP_On"
        					}
        				}
        			},
        			{
        				"infraRsLldpIfPol": {
        					"attributes": {
        						"tnLldpIfPolName": "LLDP_On"
        					}
        				}
        			},
                    {
                    	"infraRsAttEntP": {
                    		"attributes": {
                    			"annotation": "",
                    			"tDn": f"uni/infra/attentp-{aep}"
                    		}
                    	}
                    }
        		]
        	}
        }
    }

    url = f'https://{ip}/api/mo/uni.json?challenge={token}'

    for policy_name, policy_data in policies.items():
        r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(policy_data))
        response_code = r.status_code
        response_text = r.text
        if response_code != 200:
            logging.error(f'failed to create application policy {policy_name} with code {response_code}')
            logging.debug(response_text)
            return False
    return True

def getInterfacePolicies(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token or cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/infra.json?query-target=children&challenge={token}'
        # TODO: should filter for name
    else:
        url = f'https://{ip}//api/node/mo/uni/infra.json?query-target=children&challenge={token}'
        # TODO: should filter for:
        # - name != default
        # - monPolDn == uni/fabric/monfab-default
        # &query-target-filter=eq(cdpIfPol.name,"CDP_On")

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        # TODO: manual filter
        policies = []
        if int(response['totalCount']) > 0:
            for policy in response['imdata']:
                for k, v in policy.items():
                    if name:
                        if 'name' in v['attributes'] and v['attributes']['name'] == name:
                            policies.append(policy)
                    elif 'name' in v['attributes'] and 'monPolDn' in v['attributes'] and v['attributes']['name'] != 'default' and v['attributes']['monPolDn'] == 'uni/fabric/monfab-default':
                        policies.append(policy)
        response['totalCount'] = len(policies)
        response['imdata'] = policies
        # TODO: end
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get policies with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Application Profiles
'''

def addAppProfile(ip = None, token = None, cookies = None, name = None, description = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{name}/ap-{name}.json?challenge={token}'
    payload = {
    	"fvAp": {
    		"attributes": {
    			"name": name
    		}
    	}
    }
    if description:
        payload['fvAp']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create application profile with code {response_code}')
        logging.debug(response_text)
        return False

def getAppProfiles(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token or cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{name}/ap-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/class/fvAp.json?challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get application profiles with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Bridge Domains
'''

def addBD(ip = None, token = None, cookies = None, name = None, description = None, tenant = None, mac = None, subnet = None, vrf = None):
    if not ip or not token or not cookies or not name or not tenant or not vrf:
        logging.error('missing ip, token, cookies, name, tenant or vrf')
        return False

    if not mac:
        mac = '00:22:BD:{:02x}:{:02x}:{:02x}'.format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    mac = mac.upper()

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{name}.json?challenge={token}'
    payload = {
    	"fvBD": {
    		"attributes": {
    			"mac": mac,
    			"name": name,
    			"arpFlood": "true",
    			"unkMacUcastAct": "flood"
    		},
    		"children": [{
				"fvRsCtx": {
					"attributes": {
						"tnFvCtxName": vrf
					}
				}
    		}]
    	}
    }

    if description:
        payload['fvBD']['attributes']['descr'] = description
    if subnet:
        payload['fvBD']['children'].append({
            "fvSubnet": {
                "attributes": {
                    "ctrl": "unspecified",
                    "ip": subnet,
                    "scope": "public",
                    "rn": f"subnet-[{subnet}]"
                }
            }
        })

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create bridge domain with code {response_code}')
        logging.debug(response_text)
        return False

def deleteBD(ip = None, token = None, cookies = None, name = None, tenant = None):
    if not ip or not token or not cookies or not name or not tenant:
        logging.error('missing ip, token, cookies, name or tenant')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{name}.json?challenge={token}'

    r = requests.delete(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        return True
    else:
        logging.error(f'failed to delete bridge domain with code {response_code}')
        logging.debug(response_text)
        return False

def getBDs(ip = None, token = None, cookies = None, tenant = None, name = None):
    if not ip or not token or not cookies or not tenant:
        logging.error('missing ip, token, cookies or tenant')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/class/fvBD.json?challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get bridge domains with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    EPG
'''

def addEPG(ip = None, token = None, cookies = None, name = None, description = None, tenant = None, bd = None, app = None, domain = None):
    if not ip or not token or not cookies or not name or not tenant or not app or not bd or not domain:
        logging.error('missing ip, token, cookies, name, tenant, app, bd or domain')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/ap-{app}/epg-{bd}.json?challenge={token}'
    payload = {
    	"fvAEPg": {
    		"attributes": {
    			"name": name,
                "pcEnfPref": "unenforced",
    		},
    		"children": [{
    			"fvRsBd": {
    				"attributes": {
    					"tnFvBDName": bd
    				}
    			}
            },
            {
                "fvRsDomAtt": {
                    "attributes": {
                        "resImedcy": "immediate",
                        "tDn": "uni/phys-Phy_Global"
                    }
                }
    		}]
    	}
    }

    if description:
        payload['fvAEPg']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create EPG with code {response_code}')
        logging.debug(response_text)
        return False

def deleteEPG(ip = None, token = None, cookies = None, name = None, tenant = None, app = None):
    if not ip or not token or not cookies or not name or not tenant or not app:
        logging.error('missing ip, token, cookies, name, tenant or app')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/ap-{app}/epg-{name}.json?challenge={token}'

    r = requests.delete(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        return True
    else:
        logging.error(f'failed to delete EPG with code {response_code}')
        logging.debug(response_text)
        return False

def getEPGs(ip = None, token = None, cookies = None, tenant = None, app = None, name = None):
    if not ip or not token or not cookies or not tenant:
        logging.error('missing ip, token, cookies, tenant or app')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/ap-{app}/epg-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/class/fvAEPg.json?challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get EPGs with code {response_code}')
        logging.debug(response_text)
        return False, False

def addPathToEPG(ip = None, token = None, cookies = None, path = None, vlan = None, mode = None, name = None, tenant = None, app = None):
    if not ip or not token or not cookies or not path or not vlan or not mode or not name or not tenant or not app:
        logging.error('missing ip, token, cookies, path, vlan, mode, name, app or tenant')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/ap-{app}/epg-{name}.json?challenge={token}'
    payload = {
    	"fvRsPathAtt": {
    		"attributes": {
    			"encap": f"vlan-{vlan}",
    			"tDn": path,
                "instrImedcy": "immediate"
    		}
    	}
    }

    if mode == 'access':
        payload['fvRsPathAtt']['attributes']['mode'] = 'native'

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to add path to EPG with code {response_code}')
        logging.debug(response_text)
        return False

'''
    Interface Policy Groups
'''

def addInterfacePolicyGroup(ip = None, token = None, cookies = None, name = None, policies = None, aep = None, description = None, attributes = {}, class_name = None):
    if not ip or not token or not cookies or not name or not aep or not class_name:
        logging.error('missing ip, token, cookies, name, class_name or aep')
        return False

    url = f'https://{ip}/api/node/mo/uni/infra/funcprof/accbundle-{name}.json?challenge={token}'
    payload = {
        class_name: {
            "attributes": {},
            "children": [{
                    "infraRsAttEntP": {
                        "attributes": {
                            "annotation": "",
                            "tDn": f"uni/infra/attentp-{aep}"
                        }
                    }
                }
            ]
        }
    }

    # Adding description
    if description:
        payload[class_name]['attributes']['descr'] = description

    # Adding custom attributes
    for k, v in attributes.items():
        payload[class_name]['attributes'][k] = v

    # Adding policies
    for policy_name in policies:
        total, objects = getInterfacePolicies(ip = ip, token = token, cookies = cookies, name = policy_name)
        if total == 1:
            policy_class_name = None
            for k, v in objects[0].items():
                # Need to capitalize first letter only
                policy_class_name = k[:1].capitalize() + k[1:]
            payload[class_name]['children'].append({
                f"infraRs{policy_class_name}": {
                    "attributes": {
                        f"tn{policy_class_name}Name": policy_name
                    }
                }
            })
        elif total > 1:
            logging.error('found multiple policies for {policy_name}')
            return False
        else:
            logging.error('policy {name} not found')
            return False

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create EPG with code {response_code}')
        logging.debug(response_text)
        return False

def getInterfacePolicyGroups(ip = None, token = None, cookies = None, name = None, class_name = None):
    if not ip or not token or not cookies or not class_name:
        logging.error('missing ip, token, cookies or class_name')
        return False, False
    # Classes:
    # - infraAccPortGrp per single port
    # - infraAccBndlGrp per port-channel/virtual port-channel

    if name:
        url = f'https://{ip}/api/node/mo/uni/infra/funcprof.json?query-target=subtree&target-subtree-class={class_name}&query-target-filter=eq({class_name}.name,"{name}")&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/infra/funcprof.json?query-target=subtree&target-subtree-class={class_name}&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get interface policy groups with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Interface Profiles
'''

def addInterfaceProfile(ip = None, token = None, cookies = None, name = None, description = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False

    url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{name}.json?challenge={token}'
    payload = {
    	"infraAccPortP": {
    		"attributes": {
    			"name": name
    		},
    		"children": []
    	}
    }

    if description:
        payload['infraAccPortP']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create interface profile with code {response_code}')
        logging.debug(response_text)
        return False

def getInterfaceProfiles(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token, cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/infra.json?query-target=subtree&target-subtree-class=infraAccPortP&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get interface profiles with code {response_code}')
        logging.debug(response_text)
        return False, False

def getSwitchProfileFromInterfaceProfile(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False, False

    url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{name}.json?query-target=subtree&target-subtree-class=infraRtAccPortP&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get switch profile from interface profiles with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Interface Selectors
'''

def addInterfaceSelector(ip = None, token = None, cookies = None, name = None, description = None, profile = None, group = None):
    if not ip or not token or not cookies or not profile or not name or not group:
        logging.error('missing ip, token, cookies, profile, group or name')
        return False

    url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{name}-typ-range.json?challenge={token}'
    payload = {
    	"infraHPortS": {
    		"attributes": {
    			"name": name
    		},
    		"children": [{
    			"infraRsAccBaseGrp": {
    				"attributes": {
    					"tDn": f"uni/infra/funcprof/accportgrp-{group}"
    				}
    			}
    		}]
    	}
    }

    if description:
        payload['infraHPortS']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create interface profile with code {response_code}')
        logging.debug(response_text)
        return False

def getInterfaceSelectors(ip = None, token = None, cookies = None, name = None, profile = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token, cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{name}-typ-range.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}.json?query-target=subtree&target-subtree-class=infraHPortS&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get interface selectors with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Interface Selector Blocks
'''

def addInterfaceSelectorBlock(ip = None, token = None, cookies = None, name = None, description = None, profile = None, selector = None):
    if not ip or not token or not cookies or not profile or not selector or not name:
        logging.error('missing ip, token, cookies, profile, selector or name')
        return False

    block_id = secrets.token_hex(8)
    url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{selector}-typ-range/portblk-{block_id}.json?challenge={token}'
    payload = {
    	"infraPortBlk": {
    		"attributes": {
    			"fromPort": name,
    			"toPort": name
    		}
    	}
    }

    if description:
        payload['infraPortBlk']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create interface selector block with code {response_code}')
        logging.debug(response_text)
        return False

def getInterfaceSelectorBlocks(ip = None, token = None, cookies = None, name = None, profile = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token, cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{name}-typ-range.json?query-target=subtree&target-subtree-class=infraPortBlk&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}.json?query-target=subtree&target-subtree-class=infraPortBlk&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get interface selector blocks with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Subnets
'''

def addSubnet(ip = None, token = None, cookies = None, name = None, description = None, tenant = None, bd = None):
    if not ip or not token or not cookies or not name or not tenant or not bd:
        logging.error('missing ip, token, cookies, name, tenant or bd')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{bd}/subnet-[{name}].json?challenge={token}'
    payload = {
		"fvSubnet": {
			"attributes": {
				"ip": name,
				"scope": "public",
				"virtual": "no"
			}
		}
    }

    if description:
        payload['fvSubnet']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create subnet with code {response_code}')
        logging.debug(response_text)
        return False

def deleteSubnet(ip = None, token = None, cookies = None, bd = None, tenant = None, name = None):
    if not ip or not token or not cookies or not name or not tenant or not bd:
        logging.error('missing ip, token, cookies, name, tenant or bd')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{bd}/subnet-[{name}].json?challenge={token}'

    r = requests.delete(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        return True
    else:
        logging.error(f'failed to delete subnet with code {response_code}')
        logging.debug(response_text)
        return False

def getSubnets(ip = None, token = None, cookies = None, tenant = None, bd = None, name = None):
    if not ip or not token or not cookies or not tenant or not bd:
        logging.error('missing ip, token, cookies, tenant or bd')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{bd}/subnet-[{name}].json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{bd}.json?query-target=children&target-subtree-class=fvSubnet&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get subnets with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Switch Profiles
'''

def bindSwitchProfileToInterfaceProfile(ip = None, token = None, cookies = None, name = None, interface_profile = None):
    if not ip or not token or not cookies or not name or not interface_profile:
        logging.error('missing ip, token, cookies, name or interface_profile')
        return False, False

    url = f'https://{ip}/api/node/mo/uni/infra/nprof-{name}.json?challenge={token}'
    payload = {
    	"infraRsAccPortP": {
    		"attributes": {
    			"tDn": f"uni/infra/accportprof-{interface_profile}"
    		}
    	}
    }

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get subnets with code {response_code}')
        logging.debug(response_text)
        return False, False

def getSwitchProfiles(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token, cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/infra/nprof-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/infra.json?query-target=subtree&target-subtree-class=infraNodeP&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get switch profiles with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    Tenants
'''

def addTenant(ip = None, token = None, cookies = None, name = None, description = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False

    url = f'https://{ip}/api/mo/uni/tn-{name}.json?challenge={token}'
    payload = {
    	"fvTenant": {
    		"attributes": {
    			"name": name
    		}
    	}
    }
    if description:
        payload['fvTenant']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create tenant with code {response_code}')
        logging.debug(response_text)
        return False

def deleteTenant(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False

    url = f'https://{ip}/api/mo/uni/tn-{name}.json?challenge={token}'

    r = requests.delete(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        return True
    else:
        logging.error(f'failed to delete tenant with code {response_code}')
        logging.debug(response_text)
        return False

def getTenants(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token or cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/mo/uni/tn-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/class/fvTenant.json?challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get tenants with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    VRF
'''

def addVRF(ip = None, token = None, cookies = None, name = None, description = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{name}/ctx-{name}.json?challenge={token}'
    payload = {
    	"fvCtx": {
    		"attributes": {
    			"name": name,
    			"pcEnfPref": "unenforced"
    		}
    	}
    }
    if description:
        payload['fvCtx']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create VRF with code {response_code}')
        logging.debug(response_text)
        return False

def getVRFs(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies:
        logging.error('missing ip, token or cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{name}/ctx-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/class/fvCtx.json?challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        total = int(response['totalCount'])
        objects = response['imdata']
        return total, objects
    else:
        logging.error(f'failed to get VRFs with code {response_code}')
        logging.debug(response_text)
        return False, False
