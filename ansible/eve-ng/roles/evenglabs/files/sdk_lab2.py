#!/usr/bin/env python2.7

import urllib3
from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.mit.request import DnQuery

urllib3.disable_warnings()

session = LoginSession('https://1.1.1.1', 'admin', 'cisco')
moDir = MoDirectory(session)
moDir.login()

dnQuery = DnQuery('uni/tn-TenantName')
dnQuery.subtree = 'children'
for tenant in moDir.query(dnQuery):
    print tenant.name
