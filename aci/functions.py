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
def getLeafID(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies, name')
        return False
    leaf_id = None

    # Finding leaf ID and POD
    url = f'https://{ip}/api/node/class/fabricNode.json?query-target-filter=and(eq(fabricNode.role,"leaf"),eq(fabricNode.name,"{name}"))&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        return response['imdata'][0]['fabricNode']['attributes']['id']
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
            return int(response['imdata'][0]['fabricPathEp']['attributes']['dn'])
        elif total > 1:
            logging.debug('found multiple leaf')
        else:
            logging.debug('leaf not found')
        return False
    else:
        logging.error(f'failed to find leaf with code {response_code}')
        logging.debug(response_text)
        return False

def getPathFromLeafName(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies, name')
        return False
    leaf_id = None
    leaf_pod = None

    # Finding leaf ID and POD
    url = f'https://{ip}/api/node/class/fabricNode.json?query-target-filter=and(eq(fabricNode.role,"leaf"),eq(fabricNode.name,"{name}"))&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        return response['imdata'][0]['fabricNode']['attributes']['dn']
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

def getEPGsFromPath(ip = None, token = None, cookies = None, leaf_path = None, port = None, fex = None):
    if not ip or not token or not cookies or not leaf_path or not port:
        logging.error('missing ip, token, cookies, leaf or port')
        return False

    if fex:
        url = f'https://{ip}/api/node/mo/{leaf_path}/sys/phys-[eth{fex}/{port}].json?rsp-subtree-include=full-deployment&target-node=all&target-path=l1EthIfToEPg&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/{leaf_path}/sys/phys-[eth{port}].json?rsp-subtree-include=full-deployment&target-node=all&target-path=l1EthIfToEPg&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        if not 'children' in response['imdata'][0]['l1PhysIf']:
            return 0, []
        try:
            objects = response['imdata'][0]['l1PhysIf']['children'][0]['pconsCtrlrDeployCtx']['children']
        except Exception as err:
            logging.debug('cannot parse EPGs from path')
            return False, False
        return len(objects), objects
    else:
        logging.error(f'failed to get EPGs with code {response_code}')
        logging.debug(response_text)
        return False, False

def getEPGsFromInterfaceProfilePath(ip = None, token = None, cookies = None, interface_profile_path = None):
    if not ip or not token or not cookies or not interface_profile_path:
        logging.error('missing ip, token, cookies, interface_profile_path')
        return False

    url = f'https://{ip}/api/node/mo/{interface_profile_path}.json?rsp-subtree-include=full-deployment&target-node=all&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        if not 'children' in response['imdata'][0]['fabricPathEp']:
            return 0, []
        try:
            objects = []
            for object in response['imdata'][0]['fabricPathEp']['children']:
                if 'children' in object['pconsNodeDeployCtx']:
                    objects.append(object)
        except Exception as err:
            logging.debug('cannot parse EPGs from path')
            return False, False
        return len(objects), objects
    else:
        logging.error(f'failed to get EPGs with code {response_code}')
        logging.debug(response_text)
        return False, False

def getPortCfgFromPath(ip = None, token = None, cookies = None, leaf_path = None, port = None, fex = None):
    if not ip or not token or not cookies or not leaf_path or not port:
        logging.error('missing ip, token, cookies, leaf or port')
        return False

    if fex:
        url = f'https://{ip}/api/node/class/{leaf_path}/l1PhysIf.json?rsp-subtree=children&rsp-subtree-class=ethpmPhysIf&query-target-filter=eq(l1PhysIf.dn,"{leaf_path}/sys/phys-[eth{fex}/{port}]")&challenge={token}'
    else:
        url = f'https://{ip}/api/node/class/{leaf_path}/l1PhysIf.json?rsp-subtree=children&rsp-subtree-class=ethpmPhysIf&query-target-filter=eq(l1PhysIf.dn,"{leaf_path}/sys/phys-[eth{port}]")&challenge={token}'

    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        cookies = r.cookies
        try:
            return response['imdata'][0]['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']
        except Exception as err:
            logging.debug('cannot parse port config from path')
            return False
    else:
        logging.error(f'failed to get port config with code {response_code}')
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
        "AEP_Global": {
    		"infraAttEntityP": {
    			"attributes": {
    				"dn": "uni/infra/attentp-AAA_AEP_Global"
    			}
    		}
        },
        "Phy_Global": {
    		"physDomP": {
    			"attributes": {
    				"dn": "uni/phys-Phy_Global"
    			},
    			"children": [{
    				"infraRsVlanNs": {
    					"attributes": {
    						"tDn": "uni/infra/vlanns-[VLAN_ALL]-static"
    					}
    				}
    			}]
    		}
        },
        "L3_Global": {
    		"l3extDomP": {
    			"attributes": {
    				"annotation": "",
    				"dn": "uni/l3dom-L3_Global",
    				"name": "L3_Global",
    				"nameAlias": "",
    				"ownerKey": "",
    				"ownerTag": ""
    			},
    			"children": [{
    				"infraRsVlanNs": {
    					"attributes": {
    						"annotation": "",
    						"tDn": "uni/infra/vlanns-[Pool_ALL_VLANs]-static"
    					}
    				}
    			}]
    		}
        },
        "VLAN_ALL": {
    		"fvnsVlanInstP": {
    			"attributes": {
    				"allocMode": "static",
    				"descr": "All VLANs except the reserved ones (1002-1005, 3967 and 4095). The VLAN 3967 is assumed to be the infrastructure VLAN.",
    				"dn": "uni/infra/vlanns-[VLAN_ALL]-static"
    			},
    			"children": [{
    				"fvnsEncapBlk": {
    					"attributes": {
    						"allocMode": "inherit",
    						"from": "vlan-3968",
    						"role": "external",
    						"to": "vlan-4094"
    					}
    				}
    			}, {
    				"fvnsEncapBlk": {
    					"attributes": {
    						"allocMode": "inherit",
    						"from": "vlan-1006",
    						"role": "external",
    						"to": "vlan-3966"
    					}
    				}
    			}, {
    				"fvnsEncapBlk": {
    					"attributes": {
    						"allocMode": "inherit",
    						"from": "vlan-1",
    						"role": "external",
    						"to": "vlan-1001"
    					}
    				}
    			}]
    		}
        },
        "VLAN_4": {
    		"fvnsVlanInstP": {
    			"attributes": {
    				"allocMode": "static",
    				"descr": "VLAN used between spines and Inter Pod Network.",
    				"dn": "uni/infra/vlanns-[VLAN_4]-static",
    				"name": "VLAN_4"
    			},
    			"children": [{
    				"fvnsEncapBlk": {
    					"attributes": {
    						"allocMode": "inherit",
    						"from": "vlan-4",
    						"role": "external",
    						"to": "vlan-4"
    					}
    				}
    			}]
    		}
        },
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

def bindBDtoL3Out(ip = None, token = None, cookies = None, name = None, tenant = None, l3out = None):
    if not ip or not token or not cookies or not name or not tenant or not l3out:
        logging.error('missing ip, token, cookies, name, tenant or l3out')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{name}.json?challenge={token}'
    payload = {
    	"fvRsBDToOut": {
    		"attributes": {
    			"tnL3extOutName": l3out
    		}
    	}
    }
    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to bind bridge domain to L3Out with code {response_code}')
        logging.debug(response_text)
        return False

def unbindBDtoL3Out(ip = None, token = None, cookies = None, name = None, tenant = None, l3out = None):
    if not ip or not token or not cookies or not name or not tenant or not l3out:
        logging.error('missing ip, token, cookies, name, tenant or l3out')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{name}.json?challenge={token}'
    payload = {
    	"fvBD": {
    		"attributes": {},
    		"children": [{
    			"fvRsBDToOut": {
    				"attributes": {
    					"dn": f"uni/tn-{tenant}/BD-{name}/rsBDToOut-{l3out}",
    					"status": "deleted"
    				}
    			}
    		}]
    	}
    }
    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to unbind bridge domain from L3Out with code {response_code}')
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
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/BD-{name}.json?rsp-subtree=full&rsp-subtree-class=fvSubnet&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}.json?query-target=children&target-subtree-class=fvBD&rsp-subtree=full&rsp-subtree-class=fvSubnet,fvRsBDToOut&challenge={token}'

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

def deletePathFromEPG(ip = None, token = None, cookies = None, path = None, name = None, tenant = None, app = None):
    if not ip or not token or not cookies or not path or not name or not tenant or not app:
        logging.error('missing ip, token, cookies, name, app or tenant or path')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/ap-{app}/epg-{name}/rspathAtt-[{path}].json?challenge={token}'
    payload = {
    	"fvRsPathAtt": {
    		"attributes": {
    			"status": "deleted"
    		}
    	}
    }

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to delete path from EPG with code {response_code}')
        logging.debug(response_text)
        return False

def getPathFromEPG(ip = None, token = None, cookies = None, tenant = None, app = None, path = None, name = None):
    if not ip or not token or not cookies or not tenant or not name or not app:
        logging.error('missing ip, token, cookies, name or tenant or app')
        return False, False

    if path:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/ap-{app}/epg-{name}.json?query-target=children&target-subtree-class=fvRsPathAtt&&query-target-filter=eq(fvRsPathAtt.tDn,"{path}")&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/ap-{app}/epg-{name}.json?query-target=children&target-subtree-class=fvRsPathAtt&challenge={token}'

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
        logging.error(f'failed to get paths from EPG with code {response_code}')
        logging.debug(response_text)
        return False, False

'''
    FEX
'''

def addFexProfile(ip = None, token = None, cookies = None, name = None, description = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies, name')
        return False

    url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{name}.json?challenge={token}'
    payload = {
    	"infraFexP": {
    		"attributes": {
    			"name": name
    		},
    		"children": [{
    			"infraFexBndlGrp": {
    				"attributes": {
    					"name": name,
                        "descr": f"Port-Channel connected to the leaf"
    				}
    			}
    		}]
    	}
    }

    # Adding description
    if description:
        payload['infraFexP']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create Fex with code {response_code}')
        logging.debug(response_text)
        return False

def getFexProfile(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies :
        logging.error('missing ip, token, cookies')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{name}/.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/infra.json?query-target=subtree&target-subtree-class=infraFexP&challenge={token}'

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
        logging.error(f'failed to get fex with code {response_code}')
        logging.debug(response_text)
        return False, False

def addFexPort(ip = None, token = None, cookies = None, fex_name = None, port = None, policy_group = None, description = None):
    if not ip or not token or not cookies or not fex_name or not port or not policy_group or not name:
        logging.error('missing ip, token, cookies, fex_name, port, policy_group or name')
        return False

    url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{fex_name}/hports-{name}-typ-range.json?challenge={token}'
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
            # Need to fix some class names
            if policy_class_name == 'LacpLagPol':
                payload[class_name]['children'].append({
                    "infraRsLacpPol": {
                        "attributes": {
                            "tnLacpLagPolName": policy_name
                        }
                    }
                })
            else:
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

def deleteInterfaceProfile(ip = None, token = None, cookies = None, name = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies, name')
        return False

    url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{name}.json?challenge={token}'

    r = requests.delete(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        return True
    else:
        logging.error(f'failed to delete interface profile with code {response_code}')
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

def getInterfaceProfileFromPortAndLeaf(ip = None, token = None, cookies = None, port = None, leaf = None):
    if not ip or not token or not cookies or not port or not leaf:
        logging.error('missing ip, token, cookies, port or leaf')
        return False
    try:
        interface_card = port.split('/')[0]
        interface_port = port.split('/')[1]
    except Exception as err:
        logging.error('port is not valid')
        return False

    url = f'https://{ip}/api/node/class/infraPortBlk.json?query-target=subtree&target-subtree-class=infraPortBlk&query-target-filter=and(le(infraPortBlk.fromCard,"{interface_card}"),ge(infraPortBlk.toCard,"{interface_card}"),le(infraPortBlk.fromPort,"{interface_port}"),ge(infraPortBlk.toPort,"{interface_port}"),wcard(infraPortBlk.dn,"^uni/infra/accportprof-"))&challenge={token}'

    # Finding interface profiles with specific port block
    r = requests.get(url, verify = False, cookies = cookies)
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        response = r.json()
        total = int(response['totalCount'])
        objects = response['imdata']
        if total is 0:
            return ''
    else:
        logging.error(f'failed to get interface profiles from port with code {response_code}')
        logging.debug(response_text)
        return False

    # Checking which interface profiles is bound to the switch profile
    for object in objects:
        interface_profile = object['infraPortBlk']['attributes']['dn'].split('/')[2].split('-')[1]
        total, unused = getSwitchProfilesFromInterfaceProfile(ip = ip, token = token, cookies = cookies, name = interface_profile, leaf = leaf)
        if total != 0:
            return interface_profile
    # Nothing found
    return ''

def getSwitchProfilesFromInterfaceProfile(ip = None, token = None, cookies = None, name = None, leaf = None):
    if not ip or not token or not cookies or not name:
        logging.error('missing ip, token, cookies or name')
        return False, False

    if not leaf:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{name}.json?query-target=subtree&target-subtree-class=infraRtAccPortP&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{name}.json?query-target=subtree&target-subtree-class=infraRtAccPortP&query-target-filter=eq(infraRtAccPortP.tDn,"uni/infra/nprof-{leaf}")&challenge={token}'

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

def addInterfaceSelector(ip = None, token = None, cookies = None, name = None, description = None, profile = None, group = None, class_name = None, fex_id = False, fex_profile_name = None):
    if not ip or not token or not cookies or not profile or not name or not group or not class_name:
        logging.error('missing ip, token, cookies, profile, group, class_name or name')
        return False
    # Classes:
    # - infraAccPortGrp per single port
    # - infraAccBndlGrp per port-channel/virtual port-channel also for Fex
    if class_name == 'infraAccPortGrp':
        object = 'accportgrp'
    elif class_name == 'infraAccBndlGrp':
        object = 'accbundle'
    else:
        logging.error('invalid class_name')
        return False

    url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{name}-typ-range.json?challenge={token}'
    payload = {
    	"infraHPortS": {
    		"attributes": {
    			"name": name
    		},
    		"children": []
    	}
    }
    if fex_id and fex_profile_name:
        payload['infraHPortS']['children'].append({
            "infraRsAccBaseGrp": {
                "attributes": {
                    "tDn": f"uni/infra/fexprof-{fex_profile_name}/fexbundle-{fex_profile_name}",
					"fexId": f"{fex_id}"
                }
            }
        })
    else:
        payload['infraHPortS']['children'].append({
            "infraRsAccBaseGrp": {
                "attributes": {
                    "tDn": f"uni/infra/funcprof/{object}-{group}"
                }
            }
        })

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

def addInterfaceSelectorBlock(ip = None, token = None, cookies = None, name = None, description = None, profile = None, selector = None, fex = False, group = None):
    if fex:
        if not ip or not token or not cookies or not profile or not selector or not name or not group:
            logging.error('missing ip, token, cookies, profile, selector, group or name')
            return False
    else:
        if not ip or not token or not cookies or not profile or not selector or not name:
            logging.error('missing ip, token, cookies, profile, selector or name')
            return False
    try:
        interface_card = name.split('/')[0]
        interface_port = name.split('/')[1]
    except Exception as err:
        logging.error('name is not valid')
        return False

    block_id = secrets.token_hex(8)
    if fex:
        object = None
        total, policy_groups = getInterfacePolicyGroups(ip = ip, token = token, cookies = cookies, name = group, class_name = 'infraAccPortGrp')
        if total > 0:
            # Policy group is for single ports
            object = 'accportgrp'
        total, policy_groups = getInterfacePolicyGroups(ip = ip, token = token, cookies = cookies, name = group, class_name = 'infraAccBndlGrp')
        if total > 0:
            # Policy group is for Port-Channel/Virtual Port-Channel
            object = 'accbundle'

        url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{profile}/hports-{selector}-typ-range.json?challenge={token}'
        payload = {
            "infraHPortS": {
                "attributes": {},
                "children": [{
                	"infraPortBlk": {
                		"attributes": {
                            "name": block_id,
                            "fromCard": interface_card,
                            "toCard": interface_card,
                			"fromPort": interface_port,
                			"toPort": interface_port
                		}
                    }
            	},
                {
        			"infraRsAccBaseGrp": {
        				"attributes": {
        					"tDn": f"uni/infra/funcprof/{object}-{group}"
        				}
                    }
    			}]
            }
        }
        if description:
            payload['infraHPortS']['children'][0]['infraPortBlk']['attributes']['descr'] = description
    else:
        url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{selector}-typ-range/portblk-{block_id}.json?challenge={token}'
        payload = {
        	"infraPortBlk": {
        		"attributes": {
                    "fromCard": interface_card,
                    "toCard": interface_card,
        			"fromPort": interface_port,
        			"toPort": interface_port
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

def deleteInterfaceSelectorBlock(ip = None, token = None, cookies = None, name = None, profile = None, selector = None, fex = False, delete_selector = False):
    if fex:
        if not ip or not token or not cookies or not profile or not selector or not name:
            logging.error('missing ip, token, cookies, profile, selector, name')
            return False
    else:
        # TODO
        logging.error('to be implemented')
        return False

    if fex:
        url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{profile}/hports-{selector}-typ-range.json?challenge={token}'
        url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{profile}/hports-{selector}-typ-range.json?challenge={token}'
        payload = {
        	"infraHPortS": {
        		"attributes": {},
        		"children": [{
        			"infraPortBlk": {
        				"attributes": {
        					"dn": f"uni/infra/fexprof-{profile}/hports-{selector}-typ-range/portblk-{name}",
        					"status": "deleted"
        				}
        			}
        		}]
        	}
        }
        if delete_selector:
            payload['infraHPortS']['attributes']['status'] = 'deleted'
    else:
        # TODO
        logging.error('to be implemented')
        return False

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to delete interface selector block with code {response_code}')
        logging.debug(response_text)
        return False

def getInterfaceSelectorBlocks(ip = None, token = None, cookies = None, name = None, profile = None, selector = None, fex = False):
    if fex:
        if not ip or not token or not cookies:
            logging.error('missing ip, token, cookies')
            return False, False
    else:
        if not ip or not token or not cookies or not selector:
            logging.error('missing ip, token, cookies, selector')
            return False, False

    if name:
        interface_card = name.split('/')[0]
        interface_port = name.split('/')[1]
        if fex and not selector:
            url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{profile}.json?query-target=subtree&target-subtree-class=infraPortBlk&target-subtree-class=infraRsAccBndlSubgrp&query-target=subtree&query-target-filter=and(le(infraPortBlk.fromCard,"{interface_card}"),ge(infraPortBlk.toCard,"{interface_card}"),le(infraPortBlk.fromPort,"{interface_port}"),ge(infraPortBlk.toPort,"{interface_port}"))&challenge={token}'
        elif fex and selector:
            url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{profile}/hports-{selector}-typ-range.json?query-target=subtree&target-subtree-class=infraPortBlk&target-subtree-class=infraRsAccBndlSubgrp&query-target=subtree&query-target-filter=and(le(infraPortBlk.fromCard,"{interface_card}"),ge(infraPortBlk.toCard,"{interface_card}"),le(infraPortBlk.fromPort,"{interface_port}"),ge(infraPortBlk.toPort,"{interface_port}"))&challenge={token}'
        else:
            url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{selector}-typ-range.json?query-target=subtree&target-subtree-class=infraPortBlk&target-subtree-class=infraRsAccBndlSubgrp&query-target=subtree&query-target-filter=and(le(infraPortBlk.fromCard,"{interface_card}"),ge(infraPortBlk.toCard,"{interface_card}"),le(infraPortBlk.fromPort,"{interface_port}"),ge(infraPortBlk.toPort,"{interface_port}"))&challenge={token}'
    else:
        if fex and not selector:
            url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{profile}.json?query-target=subtree&target-subtree-class=infraPortBlk&target-subtree-class=infraRsAccBndlSubgrp&query-target=subtree&challenge={token}'
        elif fex and selector:
            url = f'https://{ip}/api/node/mo/uni/infra/fexprof-{profile}/hports-{selector}-typ-range.json?query-target=subtree&target-subtree-class=infraPortBlk&target-subtree-class=infraRsAccBndlSubgrp&query-target=subtree&challenge={token}'
        else:
            url = f'https://{ip}/api/node/mo/uni/infra/accportprof-{profile}/hports-{selector}-typ-range.json?query-target=subtree&target-subtree-class=infraPortBlk&target-subtree-class=infraRsAccBndlSubgrp&query-target=subtree&challenge={token}'

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
    L3 OUTS
'''

def addStaticL3Out(ip = None, token = None, cookies = None, name = None, description = None, tenant = None, vrf = None, domain = None):
    if not ip or not token or not cookies or not name or not tenant or not vrf or not domain:
        logging.error('missing ip, token, cookies, name, tenant, vrf or domain')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{name}.json?challenge={token}'
    payload = {
    	"l3extOut": {
    		"attributes": {
    			"name": name,
                "enforceRtctrl": "export"
    		},
    		"children": [{
    			"l3extRsEctx": {
    				"attributes": {
    					"tnFvCtxName": vrf
    				}
    			}
    		}, {
    			"l3extRsL3DomAtt": {
    				"attributes": {
    					"tDn": f"uni/l3dom-{domain}",
    				}
    			}
            }, {
				"l3extInstP": {
					"attributes": {
						"floodOnEncap": "disabled",
						"matchT": "AtleastOne",
						"name": "ALL_Prefixes",
						"prefGrMemb": "exclude",
						"prio": "unspecified",
						"targetDscp": "unspecified"
					}
				}
    		}]
    	}
    }

    if description:
        payload['l3extOut']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create subnet with code {response_code}')
        logging.debug(response_text)
        return False

def getL3Outs(ip = None, token = None, cookies = None, tenant = None, name = None):
    if not ip or not token or not cookies or not tenant:
        logging.error('missing ip, token, cookies, tenant')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}.json?query-target=children&target-subtree-class=l3extOut&query-target-filter=not(wcard(l3extOut.name,"__ui_"))&challenge={token}'

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
        logging.error(f'failed to get L3Outs with code {response_code}')
        logging.debug(response_text)
        return False, False

def addStaticL3OutSVI(ip = None, token = None, cookies = None, tenant = None, path = None, group = None, vip_mac_address = None, vlan = None, leaf_ip = None, vip_ip_address = None, mode = None, l3out = None, node_name = None, name = None):
    if not ip or not token or not cookies or not tenant or not path or not vlan or not leaf_ip or not vip_ip_address or not mode or not l3out or not node_name or not name or not mode:
        logging.error('missing ip, token, cookies, tenant, vlan, leaf_ip, vip_ip_address, mode, l3out, node_name, name')
        return False
    if not path and not group:
        logging.error('path or group must be specified')
        return False

    if not vip_mac_address:
        vip_mac_address = '00:22:BD:{:02x}:{:02x}:{:02x}'.format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    if path:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/lifp-{name}/rspathL3OutAtt-[{path}].json?challenge={token}'

        payload = {
        	"l3extRsPathL3OutAtt": {
        		"attributes": {
        			"mac": vip_mac_address,
        			"ifInstT": "ext-svi",
        			"encap": f"vlan-{vlan}",
        			"addr": leaf_ip
        		},
        		"children": [{
        			"l3extIp": {
        				"attributes": {
        					"addr": vip_ip_address
        				}
        			}
        		}]
        	}
        }

        if mode == 'access':
            payload['l3extRsPathL3OutAtt']['attributes']['mode'] = 'native'
    if group:
        # TODO: need to be implemented
        logging.error('not implemented')
        return False

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create static L3Out SVI with code {response_code}')
        logging.debug(response_text)
        return False

def getStaticL3OutSVI(ip = None, token = None, cookies = None, tenant = None, l3out = None, node_name = None, interface_name = None, path = None, group = None):
    if not ip or not token or not cookies or not tenant or not l3out or not node_name or not interface_name:
        logging.error('missing ip, token, cookies, tenant, l3out, node_name, interface_name')
        return False, False

    if path:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/lifp-{interface_name}.json?query-target=subtree&target-subtree-class=l3extRsPathL3OutAtt&query-target-filter=eq(l3extRsPathL3OutAtt.tDn,"{path}")&challenge={token}'
    elif group:
        # TODO: need to be implemented
        logging.error('not implemented')
        return False, False
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/lifp-{interface_name}.json?query-target=subtree&target-subtree-class=l3extRsPathL3OutAtt&challenge={token}'

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
        logging.error(f'failed to get SVI from L3Out with code {response_code}')
        logging.debug(response_text)
        return False, False

def addL3OutNodeProfile(ip = None, token = None, cookies = None, name = None, description = None, l3out = None, tenant = None):
    if not ip or not token or not cookies or not name or not tenant or not l3out or not tenant:
        logging.error('missing ip, token, cookies, name, tenant, l3out')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{name}.json?challenge={token}'
    payload = {
    	"l3extLNodeP": {
    		"attributes": {
    			"name": name
    		}
    	}
    }

    if description:
        payload['l3extLNodeP']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create L3Out node profile with code {response_code}')
        logging.debug(response_text)
        return False

def getL3OutNodeProfiles(ip = None, token = None, cookies = None, tenant = None, l3out = None, name = None):
    if not ip or not token or not cookies or not tenant or not l3out:
        logging.error('missing ip, token, cookies, tenant, l3out')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{name}.json?challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}.json?query-target=children&target-subtree-class=l3extLNodeP&query-target-filter=not(wcard(l3extLNodeP.name,"__ui_"))&challenge={token}'

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
        logging.error(f'failed to get L3Out node profiles with code {response_code}')
        logging.debug(response_text)
        return False, False

def addL3OutNodeInterfaceProfile(ip = None, token = None, cookies = None, name = None, description = None, l3out = None, tenant = None, node = None):
    if not ip or not token or not cookies or not name or not tenant or not l3out or not node:
        logging.error('missing ip, token, cookies, name, tenant, l3out, node')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node}/lifp-{name}.json?challenge={token}'
    payload = {
    	"l3extLIfP": {
    		"attributes": {
    			"name": name
    		}
    	}
    }

    if description:
        payload['l3extLIfP']['attributes']['descr'] = description

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create L3Out node interface profile with code {response_code}')
        logging.debug(response_text)
        return False

def getL3OutNodeInterfaceProfiles(ip = None, token = None, cookies = None, tenant = None, l3out = None, node = None, name = None):
    if not ip or not token or not cookies or not tenant or not l3out or not node:
        logging.error('missing ip, token, cookies, tenant, l3out, node')
        return False, False

    if name:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node}.json?query-target=children&target-subtree-class=l3extLIfP&query-target-filter=eq(l3extLIfP.name,"{name}")&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node}.json?query-target=subtree&target-subtree-class=l3extLIfP&query-target-filter=not(wcard(l3extLIfP.name,"__ui_"))&challenge={token}'

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
        logging.error(f'failed to get L3Out node interface profiles with code {response_code}')
        logging.debug(response_text)
        return False, False


def addStaticL3OutConfiguredNodes(ip = None, token = None, cookies = None, tenant = None, l3out = None, node_name = None, path = None, router_id = None):
    if not ip or not token or not cookies or not tenant or not l3out or not node_name or not path or not router_id:
        logging.error('missing ip, token, cookies, tenant, l3out, node')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/rsnodeL3OutAtt-[{path}].json?challenge={token}'
    payload = {
	"l3extRsNodeL3OutAtt": {
    		"attributes": {
    			"rtrId": router_id,
    			"rtrIdLoopBack": "false"
    		}
    	}
    }

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create L3Out node configuration with code {response_code}')
        logging.debug(response_text)
        return False

def getStaticL3OutConfiguredNodes(ip = None, token = None, cookies = None, tenant = None, l3out = None, node_name = None, path = None):
    if not ip or not token or not cookies or not tenant or not l3out or not node_name:
        logging.error('missing ip, token, cookies, tenant, l3out, node_name')
        return False, False

    if path:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}.json?query-target=children&target-subtree-class=l3extRsNodeL3OutAtt&query-target-filter=eq(l3extRsNodeL3OutAtt.tDn,"{path}")&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}.json?query-target=children&target-subtree-class=l3extRsNodeL3OutAtt&rsp-subtree=full&challenge={token}'

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
        logging.error(f'failed to get L3Out configured nodes with code {response_code}')
        logging.debug(response_text)
        return False, False

def addStaticRoute(ip = None, token = None, cookies = None, tenant = None, l3out = None, node_name = None, path = None, network = None, gateway = None):
    if not ip or not token or not cookies or not tenant or not l3out or not node_name or not gateway:
        logging.error('missing ip, token, cookies, tenant, l3out, node_name, gateway')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/rsnodeL3OutAtt-[{path}]/rt-[{network}].json?challenge={token}'
    payload = {
    	"ipRouteP": {
    		"attributes": {},
    		"children": [{
    			"ipNexthopP": {
    				"attributes": {
    					"dn": f"uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/rsnodeL3OutAtt-[{path}]/rt-[{network}]/nh-[{gateway}]",
    					"pref": "1"
    				}
    			}
    		}]
    	}
    }

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to create static route with code {response_code}')
        logging.debug(response_text)
        return False

def deleteStaticRoute(ip = None, token = None, cookies = None, tenant = None, l3out = None, node_name = None, path = None, network = None):
    if not ip or not token or not cookies or not tenant or not l3out or not node_name:
        logging.error('missing ip, token, cookies, tenant, l3out, node_name')
        return False

    url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/rsnodeL3OutAtt-[{path}].json?challenge={token}'
    payload = {
        "l3extRsNodeL3OutAtt": {
            "attributes": {},
            "children": [{
            	"ipRouteP": {
            		"attributes": {
                        "ip": network,
                        "status": "deleted"
                    }
            	}
            }]
        }
    }

    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(payload))
    response_code = r.status_code
    response_text = r.text
    if response_code == 200:
        return True
    else:
        logging.error(f'failed to delete static route with code {response_code}')
        logging.debug(response_text)
        return False

def getStaticRoutes(ip = None, token = None, cookies = None, tenant = None, l3out = None, node_name = None, path = None, network = None):
    if not ip or not token or not cookies or not tenant or not l3out or not node_name:
        logging.error('missing ip, token, cookies, tenant, l3out, node_name')
        return False, False

    if network:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/rsnodeL3OutAtt-[{path}].json?query-target=subtree&target-subtree-class=ipRouteP&rsp-subtree=children&query-target-filter=eq(ipRouteP.ip,"{network}")&challenge={token}'
    else:
        url = f'https://{ip}/api/node/mo/uni/tn-{tenant}/out-{l3out}/lnodep-{node_name}/rsnodeL3OutAtt-[{path}].json?query-target=subtree&target-subtree-class=ipRouteP&rsp-subtree=children&challenge={token}'

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
        logging.error(f'failed to get static routes with code {response_code}')
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
        logging.error(f'failed to bind switch profile to interface profile with code {response_code}')
        logging.debug(response_text)
        return False, False

def unbindSwitchProfileFromInterfaceProfile(ip = None, token = None, cookies = None, name = None, interface_profile = None):
    if not ip or not token or not cookies or not name or not interface_profile:
        logging.error('missing ip, token, cookies, name or interface_profile')
        return False, False

    url = f'https://{ip}/api/node/mo/uni/infra/nprof-{name}.json?challenge={token}'
    payload = {
    	"infraRsAccPortP": {
    		"attributes": {
    			"tDn": f"uni/infra/accportprof-{interface_profile}",
                "status": "deleted"
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
        logging.error(f'failed to unbind switch profile from interface profile with code {response_code}')
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
