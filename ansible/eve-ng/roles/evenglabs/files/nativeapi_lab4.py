#!/usr/bin/env python3

from zeep.cache import SqliteCache
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

# Defining request data
listUser = {
    'searchCriteria': {
        'lastName': '%'
    },
    'returnedTags': {
        'firstName': '',
        'lastName': '',
        'userid': '',
        'telephoneNumber': ''
    }
}

# Configure logging
logging.basicConfig()
logger = logging.getLogger()
zeep_transport_logger = logging.getLogger('zeep.transports')
logger.setLevel(logging.ERROR)

try:
    users = axl.listUser(**listUser)['return']['user']
except zeep.exceptions.Fault:
    logger.error('failed to get users via SOAP request', exc_info = True)
    for hist in [history.last_sent, history.last_received]:
        logging.debug(lxml.etree.tostring(hist['envelope'], encoding = 'unicode', pretty_print = True))

print(users)
