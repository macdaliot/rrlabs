#!/usr/bin/env python3
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://www.gnu.org/licenses/gpl.html'
__revision__ = '20170329'

import configparser, flask, json, logging, os, random

working_dir = os.path.dirname(os.path.abspath(__file__))
app = flask.Flask(__name__)

discovery_output = 'discovery_output.json'
devices_file = 'devices.ini'

if not os.path.isfile(discovery_output):
    logging.error('inventory file does not exist ({})'.format(discovery_output))
    sys.exit(255)
try:
    links = json.load(open(discovery_output))
except:
    logging.error('cannot read inventory file ({})'.format(discovery_output))
    sys.exit(255)

device_options = configparser.ConfigParser()
device_options.read(devices_file)

def saveConfig():
    with open(devices_file, 'w') as device_fp:
        device_options.write(device_fp)

@app.route('/', methods = ['GET'])
def getPage():
    return flask.render_template('template.html', name = 'netdoc')

# curl -s -D- -X GET http://127.0.0.1:5000/api/nodes
@app.route('/api/nodes', methods = ['GET'])
def getNodes():
    nodes = {}
    for link in links:
        if not link['source'] in nodes:
            nodes[link['source']] = {}
        if not link['destination'] in nodes:
            nodes[link['destination']] = {}

    #if id and discovered_nodes.has_section(id):
    #    nodes[id] = discovered_nodes[id]
    #elif id:
    #    flask.abort(404)
    #else:
    #    for discovered_node in discovered_nodes.sections():
    #        nodes[discovered_node] = discovered_nodes[discovered_node]

    # read and merge from devices.ini

    response = {
        'code': 200,
        'status': 'success',
        'data': {}
    }

    for node in nodes:
        label = discovered_nodes[node]['label'] if discovered_nodes.has_option(node, 'label') else discovered_nodes[node]['id']
        left = discovered_nodes[node]['left'] if discovered_nodes.has_option(node, 'left') else random.randint(0, 10) * 10
        top = discovered_nodes[node]['top'] if discovered_nodes.has_option(node, 'top') else random.randint(0, 10) * 10
        response['data'][node] = {
            'disabled': discovered_nodes[node]['disabled'],
            'image': discovered_nodes[node]['image'],
            'id': discovered_nodes[node]['id'],
            'label': label,
            'left': left,
            'platform': discovered_nodes[node]['platform'],
            'top': top
        }
    return flask.jsonify(response), response['code']

# curl -s -D- -X PUT -d '{"left": 181, "top": 818"}' -H 'Content-type: application/json' http://127.0.0.1:5000/api/nodes/nodeid
@app.route('/api/nodes/<id>', methods = ['PUT'])
def putNode(id):
    if not discovered_nodes.has_section(id):
        flask.abort(404)
    data = flask.request.get_json(silent = True)
    if not data:
        flask.abort(400)
    if not 'left' in data.keys() and not 'top' in data.keys():
        flask.abort(400)
    if 'left' in data.keys():
        discovered_nodes[id]['left'] = str(data['left'])
    if 'top' in data.keys():
        discovered_nodes[id]['top'] = str(data['top'])
    saveConfig()
    return getNodes(id)

# curl -s -D- -X GET http://127.0.0.1:5000/api/connections
@app.route('/api/connections', methods = ['GET'])
def getConnections():
    response = {
        'code': 200,
        'status': 'success',
        'data': links
    }
    return flask.jsonify(response), response['code']

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000, extra_files = [devices_file, discovery_output, 'templates/template.html'], debug = True)

