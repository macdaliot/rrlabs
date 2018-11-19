#!/usr/bin/env python3

from collections import OrderedDict
from zeep.cache import SqliteCache
from zeep.helpers import serialize_object
import logging, lxml, os, requests, sys, urllib3, zeep
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

cucm = '1.1.1.1'
username = 'admin'
password = 'cisco'

binding_name = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"
wsdl_file = os.path.abspath('/usr/src/axlsqltoolkit/schema/11.0/AXLAPI.wsdl')
url = 'https://{}:8443/axl/'.format(cucm)

# Configure Zeep (for SOAP requests)
session = requests.Session()
session.verify = False
session.auth = requests.auth.HTTPBasicAuth(username, password)
transport = zeep.transports.Transport(cache = SqliteCache(), session = session, timeout = 20)
history = zeep.plugins.HistoryPlugin()
client = zeep.Client(wsdl = wsdl_file, transport = transport, plugins = [history])
axl = client.create_service(binding_name, url)

sql = "SELECT name FROM applicationuser"

try:
   # Read the CUCM Data Dictionary
   sql_result = serialize_object(axl.executeSQLQuery(sql)['return']['row'])
except zeep.exceptions.Fault:
   for hist in [history.last_sent, history.last_received]:
       print(lxml.etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))

for row in sql_result:
    for element in row:
        if element.tag == 'name':
            print(element.text)
