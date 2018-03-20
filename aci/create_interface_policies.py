#!/usr/bin/env python3
""" Create Interface Policies """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20180320'

import getopt, logging, json, requests, sys, urllib3
from login_aci import *
urllib3.disable_warnings()

# Reading options
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

username = 'admin'
password = 'rfc1918!'
apic_host = '172.25.82.1'
login_url = 'https://{}/api/aaaLogin.json?gui-token-request=yes'.format(apic_host)

token, cookies, response_code = login(url = login_url, username = username, password = password)

if response_code != 200:
    logging.error('failed to login')
    sys.exit(1)

policies = {
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

policy_groups = {
	"Connect_EndPoint_with_individual_ports": {
		"infraAccPortGrp": {
			"attributes": {
				"descr": "Connect an endpoint device without aggregation.",
				"dn": "uni/infra/funcprof/accportgrp-Connect_EndPoint_with_individual_ports"
			},
			"children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
			    {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}} # LLDP_on
			]
		}
	},
	"Connect_Switch_with_individual_ports": {
		"infraAccPortGrp": {
			"attributes": {
				"descr": "Connect a L2 switch without aggregation.",
				"dn": "uni/infra/funcprof/accportgrp-Connect_Switch_with_individual_ports"
			},
			"children": [
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
			    {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}} # LLDP_on
			]
		}
	},
	"Connect_EndPoint_with_PC_static": {
		"infraAccBndlGrp": {
			"attributes": {
				"descr": "Connect an endpoint device using a static port-channel.",
				"dn": "uni/infra/funcprof/accbundle-Connect_EndPoint_with_PC_static"
			},
			"children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
			    {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_static"}}} # PC_static
			]
		}
	},
	"Connect_Switch_with_PC_static": {
		"infraAccBndlGrp": {
			"attributes": {
				"descr": "Connect a L2 switch using a static port-channel.",
				"dn": "uni/infra/funcprof/accbundle-Connect_Switch_with_PC_static"
			},
			"children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
			    {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_static"}}} # PC_static
			]
		}
	},
	"Connect_EndPoint_with_PC_LACP": {
		"infraAccBndlGrp": {
			"attributes": {
				"descr": "Connect an endpoint device using a LACP port-channel.",
				"dn": "uni/infra/funcprof/accbundle-Connect_EndPoint_with_PC_LACP"
			},
			"children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
			    {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_LACP"}}} # PC_LACP
			]
		}
	},
	"Connect_EndPoint_with_PC_LACP_no_suspend": {
		"infraAccBndlGrp": {
			"attributes": {
				"descr": "Connect an endpoint device using a LACP port-channel. Individual interfaces are not suspended.",
				"dn": "uni/infra/funcprof/accbundle-Connect_EndPoint_with_PC_LACP_no_suspend"
			},
			"children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
			    {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_LACP_no_suspend"}}} # PC_LACP_no_suspend
			]
		}
	},
	"Connect_Switch_with_PC_LACP": {
		"infraAccBndlGrp": {
			"attributes": {
				"descr": "Connect a L2 switch using a LACP port-channel.",
				"dn": "uni/infra/funcprof/accbundle-Connect_Switch_with_PC_LACP"
			},
			"children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
			    {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_LACP"}}} # PC_LACP
			]
		}
	},
    "Connect_EndPoint_with_vPC_LACP": {
        "infraAccBndlGrp": {
            "attributes": {
                "descr": "Connect an endpoint device using a LACP virtual port-channel.",
                "dn": "uni/infra/funcprof/accbundle-Connect_EndPoint_with_vPC_LACP",
                "lagT": "node"
            },
            "children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
                {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_LACP"}}} # PC_LACP
            ]
        }
    },
    "Connect_EndPoint_with_vPC_LACP_no_suspend": {
        "infraAccBndlGrp": {
            "attributes": {
                "descr": "Connect an endpoint device using a LACP virtual port-channel. Individual interfaces are not suspended.",
                "dn": "uni/infra/funcprof/accbundle-Connect_EndPoint_with_vPC_LACP_no_suspend",
                "lagT": "node"
            },
            "children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
                {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_LACP_no_suspend"}}} # PC_LACP_no_suspend
            ]
        }
    },
    "Connect_Switch_with_vPC_LACP": {
        "infraAccBndlGrp": {
            "attributes": {
                "descr": "Connect a L2 switch using a LACP virtual port-channel.",
                "dn": "uni/infra/funcprof/accbundle-Connect_Switch_with_vPC_LACP",
                "lagT": "node"
            },
            "children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "BPDU_guard"}}}, # BPDU_guard
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "CDP_on"}}}, # CDP_on
                {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "LLDP_on"}}}, # LLDP_on
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "PC_LACP"}}} # PC_LACP
            ]
        }
    }
}

url = 'https://{}/api/mo/uni.json?challenge={}'.format(apic_host, token)

for policy_name in policies:
    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(policies[policy_name]))
    response = r.json()
    response_code = r.status_code
    if response_code != 200:
        logging.error('failed to add interface policy "{}"'.format(policy_name))

for policy_group_name in policy_groups:
    r = requests.post(url, verify = False, cookies = cookies, data = json.dumps(policy_groups[policy_group_name]))
    response = r.json()
    response_code = r.status_code
    if response_code != 200:
        logging.error('failed to add interface policy group "{}"'.format(policy_group_name))
