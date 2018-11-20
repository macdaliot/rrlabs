#!/usr/bin/env python2.7

import urllib3
from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession

urllib3.disable_warnings()

session = LoginSession('https://1.1.1.1', 'admin', 'cisco')
moDir = MoDirectory(session)
moDir.login()

fvTenant_objects = moDir.lookupByClass('fvTenant')
for tenant in fvTenant_objects:
    print tenant.name
