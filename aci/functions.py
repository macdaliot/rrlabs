#!/usr/bin/env python3
""" Functions for Cisco ACI """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20180320'

import getopt, json, logging, random, requests, urllib3, sys, textwrap

urllib3.disable_warnings()

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('')
    print('Options:')
    print('    -d             enable debug')
    print('    -u username    the username for the APIC controller')
    print('    -p password    the password for the APIC controller')
    print('    -h hostname    the hostname or IP of the APIC controller')

def addApplicationProfile(apic_host = None, token = None, cookies = None, tenant_name = None, name = None, description = None):
    url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)
    if not tenant_name:
        tenant_name = 'common'
    if not description:
        description = 'Application Profile {}'.format(tenant_name)
    else:
        description = fixDescription(description)

    data = {
    	"fvAp": {
    		"attributes": {
    			"descr": description,
    			"dn": "uni/tn-{}/ap-{}".format(tenant_name, name),
    			"prio": "unspecified"
    		}
    	}
    }
    try:
        r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(data))
        response = r.json()
        response_code = r.status_code
    except Exception as err:
        logging.error(err)
        response_code = 0;
        response = {}
        pass
    return response_code, response

def addBridgeDomain(apic_host = None, token = None, cookies = None, tenant_name = None, name = None, description = None, mac_address = None, igmp_snooping = False, vrf = None):
    url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)
    if not tenant_name:
        tenant_name = 'common'
    if not description:
        description = 'Bridge Domain {}'.format(name)
    else:
        description = fixDescription(description)
    if not mac_address:
        mac_address = '00:22:BD:{:X}:{:X}:{:X}'.format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    if igmp_snooping:
        igmp_snoop_policy = 'IGMP_Snoop_on'
    else:
        igmp_snoop_policy = 'IGMP_Snoop_off'
    if not vrf:
        vrf = 'default'

    data = {
    	"totalCount": "1",
    	"imdata": [{
    		"fvBD": {
    			"attributes": {
    				"OptimizeWanBandwidth": "no",
    				"arpFlood": "yes",
    				"descr": description,
    				"dn": "uni/tn-{}/BD-{}".format(tenant_name, name),
    				"epClear": "no",
    				"intersiteBumTrafficAllow": "no",
    				"intersiteL2Stretch": "no",
    				"ipLearning": "yes",
    				"limitIpLearnToSubnets": "yes",
    				"mac": mac_address,
    				"mcastAllow": "no",
    				"multiDstPktAct": "bd-flood",
    				"type": "regular",
    				"unicastRoute": "yes",
    				"unkMacUcastAct": "flood",
    				"unkMcastAct": "flood",
    				"vmac": "not-applicable"
    			},
    			"children": [{
    				"fvRsIgmpsn": {
    					"attributes": {
    						"tnIgmpSnoopPolName": igmp_snoop_policy
    					}
    				}
    			}, {
                    "fvRsCtx": {
                        "attributes": {
                            "tnFvCtxName": vrf
                        }
                    }
                }, {
    				"fvRsBdToEpRet": {
    					"attributes": {
    						"resolveAct": "resolve",
    						"tnFvEpRetPolName": ""
    					}
    				}
    			}, {
    				"fvRsBDToNdP": {
    					"attributes": {
    						"tnNdIfPolName": ""
    					}
    				}
    			}]
    		}
    	}]
    }

    try:
        r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(data))
        response = r.json()
        response_code = r.status_code
    except Exception as err:
        logging.error(err)
        response_code = 0;
        response = {}
        pass
    return response_code, response


def addDefaultPolicies(apic_host = None, token = None, cookies = None):
    url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)
    policies = {
        "IGMP_Snoop_off": {
    		"igmpSnoopPol": {
    			"attributes": {
    				"adminSt": "disabled",
    				"descr": "Disable IGMP Snooping.",
    				"dn": "uni/tn-common/snPol-IGMP_Snoop_off",
    				"lastMbrIntvl": "1",
    				"queryIntvl": "125",
    				"rspIntvl": "10",
    				"startQueryCnt": "2",
    				"startQueryIntvl": "31"
    			}
    		}
        },
        "IGMP_Snoop_on": {
    		"igmpSnoopPol": {
    			"attributes": {
    				"adminSt": "enabled",
    				"descr": "Enable IGMP Snooping.",
    				"dn": "uni/tn-common/snPol-IGMP_Snoop_on",
    				"lastMbrIntvl": "1",
    				"queryIntvl": "125",
    				"rspIntvl": "10",
    				"startQueryCnt": "2",
    				"startQueryIntvl": "31"
    			}
    		}
        },
    	"CDP": {
    		"cdpIfPol": {
    			"attributes": {
    				"adminSt": "enabled",
    				"descr": "Enable CDP protocol.",
    				"dn": "uni/infra/cdpIfP-CDP_on"
    			}
    		}
    	},
    	"LLDP": {
    		"lldpIfPol": {
    			"attributes": {
    				"adminRxSt": "enabled",
    				"adminTxSt": "enabled",
    				"descr": "Enable LLDP protocol.",
    				"dn": "uni/infra/lldpIfP-LLDP_on"
    			}
    		}
    	},
    	"LACP_active": {
    		"lacpLagPol": {
    			"attributes": {
    				"ctrl": "fast-sel-hot-stdby,graceful-conv,susp-individual",
    				"descr": "Port-Channel with LACP in active mode.",
    				"dn": "uni/infra/lacplagp-PC_LACP",
    				"maxLinks": "16",
    				"minLinks": "1",
    				"mode": "active"
    			}
    		}
    	},
    	"LACP_active_no_suspend": {
    		"lacpLagPol": {
    			"attributes": {
    				"ctrl": "fast-sel-hot-stdby,graceful-conv",
    				"descr": "Port-Channel with LACP in active mode. Individual interfaces are not suspended.",
    				"dn": "uni/infra/lacplagp-PC_LACP_no_suspend",
    				"maxLinks": "16",
    				"minLinks": "1",
    				"mode": "off"
    			}
    		}
    	},
    	"LACP_static": {
    		"lacpLagPol": {
    			"attributes": {
    				"ctrl": "fast-sel-hot-stdby,graceful-conv,susp-individual",
    				"descr": "Static Port-Channel.",
    				"dn": "uni/infra/lacplagp-PC_static",
    				"maxLinks": "16",
    				"minLinks": "1",
    				"mode": "off"
    			}
    		}
    	},
    	"BPDU_guard": {
    		"stpIfPol": {
    			"attributes": {
    				"ctrl": "bpdu-guard",
    				"descr": "Shutdown if receiving BPDU.",
    				"dn": "uni/infra/ifPol-BPDU_guard"
    			}
    		}
    	},
    	"BPDU_filter": {
    		"stpIfPol": {
    			"attributes": {
    				"ctrl": "bpdu-filter",
    				"descr": "Filter incoming BPDU.",
    				"dn": "uni/infra/ifPol-BPDU_filter"
    			}
    		}
    	}
    }

    for policy_name, policy_data in policies.items():
        try:
            r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(policy_data))
            response = r.json()
            response_code = r.status_code
        except Exception as err:
            logging.error('{}: {}', policy_name, err)
            response_code = 0;
            response = {}
            return False
    return True

def addTenant(apic_host = None, token = None, cookies = None, name = None, description = None):
    url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)
    if not description:
        description = 'Tenant {}'.format(tenant)
    else:
        description = fixDescription(description)

    data = {
    	"fvTenant": {
    		"attributes": {
    			"descr": description,
    			"dn": "uni/tn-{}".format(name)
    		}
    	}
    }
    try:
        r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(data))
        response = r.json()
        response_code = r.status_code
    except Exception as err:
        logging.error(err)
        response_code = 0;
        response = {}
        pass
    return response_code, response

def addVRF(apic_host = None, token = None, cookies = None, tenant_name = None, name = None, description = None, enforced = False):
    url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)
    if not tenant_name:
        tenant_name = 'common'
    if not description:
        description = 'VRF {}'.format(name)
    else:
        description = fixDescription(description)
    if enforced:
        enforced = 'enforced'
    else:
        enforced = 'unenforced'

    data = {
    	"fvCtx": {
    		"attributes": {
    			"bdEnforcedEnable": "no",
    			"descr": description,
    			"dn": "uni/tn-{}/ctx-{}".format(tenant_name, name),
    			"knwMcastAct": "permit",
    			"pcEnfDir": "ingress",
    			"pcEnfPref": enforced
    		}
    	}
    }
    try:
        r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(data))
        response = r.json()
        response_code = r.status_code
    except Exception as err:
        logging.error(err)
        response_code = 0;
        response = {}
        pass
    return response_code, response

def checkOpts():
    username = None
    password = None
    apic_host = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'du:p:h:')
    except getopt.GetoptError as err:
        logging.error(err)
        usage()
        sys.exit(255)
    for opt, arg in opts:
        if opt == '-d':
            logging.basicConfig(level = logging.DEBUG)
        elif opt == '-u':
            username = arg
        elif opt == '-p':
            password = arg
        elif opt == '-h':
            apic_host = arg
        else:
            assert False, 'unhandled option'

    # Checking options
    if username == None:
        logging.error('username not set')
        usage()
        sys.exit(255)
    if password == None:
        logging.error('password not set')
        usage()
        sys.exit(255)
    if apic_host == None:
        logging.error('APIC not set')
        usage()
        sys.exit(255)
    return username, password, apic_host

def fixDescription(description = ""):
    description = textwrap.shorten(description, width = 125, placeholder = '...')
    description = description.replace("'", ' ')
    return description

def login(username = None, password = None, apic_host = None):
    url = 'https://{}/api/aaaLogin.json?gui-token-request=yes'.format(apic_host)
    if not username or not password or not apic_host:
        return None, False, None
    payload = {
      "aaaUser": {
        "attributes": {
          "name": username,
          "pwd": password
        }
      }
    }

    try:
        r = requests.post(url, verify = False, data = json.dumps(payload))
        response = r.json()
        response_code = r.status_code
        cookies = r.cookies
        token = response['imdata'][0]['aaaLogin']['attributes']['urlToken']
    except Exception as err:
        logging.error(err)
        token = None
        pass
    return token, cookies, response_code
