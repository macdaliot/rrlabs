#!/usr/bin/env python3.5

import io

class FilterModule(object):
    def filters(self):
        return {
            'a_filter': self.a_filter,
            'another_filter': self.b_filter,
            'show_cdp_neighbors_to_json': self.cli_cdp_to_json
        }
 
    def a_filter(self, a_variable):
        a_new_variable = a_variable + ' CRAZY NEW FILTER'
        return a_new_variable

    def b_filter(self, a_variable, another_variable, yet_another_variable):
        a_new_variable = a_variable + ' - ' + another_variable + ' - ' + yet_another_variable
        return a_new_variable

    def cli_cdp_to_json(self, cli_output):
	cli_output = """Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone,
                  D - Remote, C - CVTA, M - Two-port Mac Relay

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
AccessServer     Gig 2/0/48        132                    2610      Eth 0/0
SIP30E4DB811EF5  Gig 1/0/27        125              H P   IP Phone  Port 1
SEP0C1167025364  Gig 1/0/15        127              H P   CTS-CODEC gbe0
SEPA0F8496BF1E5  Gig 2/0/25        167              H P   CTS-CODEC eth0
SEP00FEC8607B3E  Gig 1/0/43        144              H P   CTS-CODEC eth0
SEP0062ECB1057E  Gig 2/0/35        127              H P   CTS-CODEC eth0
SEP84B2611EDC34  Gig 1/0/10        159             H P M  IP Phone  Port 1
swistellapd001.campus.infocert.it
                 Ten 1/0/1         160             R S I  WS-C4500X Ten 1/1/4
swistellapd001.campus.infocert.it
                 Ten 2/0/1         164             R S I  WS-C4500X Ten 2/1/4
ITPD2APPIA09002.corp.infocert.it
                 Gig 1/0/2         135             T B I  AIR-CAP27 Gig 0.1
ITPD2APPIA09004.corp.infocert.it
                 Gig 1/0/3         147             T B I  AIR-CAP27 Gig 0.1
ITPD2APPIA09007.corp.infocert.it
                 Gig 1/0/1         125             T B I  AIR-CAP27 Gig 0.1

Total cdp entries displayed : 12"""
        cdp_neighbors = {}
        buf = io.StringIO(cli_output)
        #for line in buf.readline():
        #    print(line)
        #    print("OK")

        return cdp_neighbors
