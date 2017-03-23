#!/usr/bin/env python3
""" API modules """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

import configparser, flask, flask_sqlalchemy, functools, hashlib, logging, memcache, os.path, pickle

CONFIG_FILE = '/data/etc/controller.ini'

# Loading config file
config = configparser.ConfigParser()
if os.path.isfile(CONFIG_FILE):
    config.read(CONFIG_FILE)
else:
    config['controller'] = {
        'id': 0,
        'db_host': '127.0.0.1',
        'db_username': 'root',
        'db_password': '',
        'db_name': 'unetlab',
        'path_labs': '/data/labs',
        'lab_extension': 'unl'
    }
    with open(CONFIG_FILE, 'w') as config_fd:
        config.write(config_fd)

# Setting environment
CONTROLLER_ID = int(config['controller']['id'])
DB_HOST = config['controller']['db_host']
DB_USERNAME = config['controller']['db_username']
DB_PASSWORD = config['controller']['db_password']
DB_NAME = config['controller']['db_name']
PATH_LABS = config['controller']['path_labs']
LAB_EXTENSION = config['controller']['lab_extension']

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/{}'.format(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME)
db = flask_sqlalchemy.SQLAlchemy(app)
cache = memcache.Client(['127.0.0.1:11211'], debug = 0)

roles_to_users = db.Table(
    'roles_to_users',
    db.Column('role', db.String(255), db.ForeignKey('roles.role')),
    db.Column('username', db.String(255), db.ForeignKey('users.username')),
)

class ActiveNode(db.Model):
    __tablename__ = 'active_nodes'
    username = db.Column(db.String, db.ForeignKey('users.username'), primary_key = True)
    lab_id = db.Column(db.String, db.ForeignKey('labs.id'), primary_key = True)
    node_id = db.Column(db.Integer, primary_key = True)
    state = db.Column(db.String(255))
    label = db.Column(db.Integer, unique = True)
    controller = db.Column(db.Integer, db.ForeignKey('controllers.id'))
    def __repr__(self):
        return '<ActiveNode(lab_id={},node_id={})>'.format(self.lab_id, self.node_id)

class ActiveTopology(db.Model):
    __tablename__ = 'active_topologies'
    username = db.Column(db.String, db.ForeignKey('users.username'), db.ForeignKey('users.username'))
    lab_id = db.Column(db.String, db.ForeignKey('users.username'), db.ForeignKey('labs.id'))
    src_id = db.Column(db.Integer, db.ForeignKey('active_nodes.label'), primary_key = True)
    src_if = db.Column(db.Integer)
    dst_id = db.Column(db.Integer, db.ForeignKey('active_nodes.label'), primary_key = True)
    dst_if = db.Column(db.Integer)
    def __repr__(self):
        return '<Topology(src_id={}:{},dst_id={}:{}>'.format(self.src_id, self_src_if, self.dst_id, self.dst_if)

class Controller(db.Model):
    __tablename__ = 'controllers'
    id = db.Column(db.String(255), primary_key = True)
    inside_ip = db.Column(db.String(255))
    outside_ip = db.Column(db.String(255))
    master = db.Column(db.Boolean)
    def __repr__(self):
        return '<Controller(id={})>'.format(self.id)

class Ethernet:
    type = 'ethernet'
    def __repr__(self):
        return '<Ethernet(id={}>'.format(self.id)
    def __init__(self, id = id, name = None, mac = None, network_id = None):
        self.id = id
        self.name = name
        self.mac = mac
        self.network_id = network_id

class Lab(db.Model):
    __tablename__ = 'labs'
    id = db.Column(db.String(255), primary_key = True)
    name = db.Column(db.String(255))
    filename = db.Column(db.String(255))
    path = db.Column(db.String(255))
    def __repr__(self):
        return '<Lab(id={})>'.format(self.id)
    @flask_sqlalchemy.orm.reconstructor

    def init_on_load(self):
        import xml.etree.ElementTree as ElementTree
        xml = ElementTree.parse('{}{}/{}'.format(PATH_LABS, self.path, self.filename))
        xml_root = xml.getroot()
        self.author = xml_root.attrib['author'] if 'author' in xml_root.attrib.keys() else None
        self.body = xml_root.attrib['body'] if 'body' in xml_root.attrib.keys() else None
        self.description = xml_root.attrib['description'] if 'description' in xml_root.attrib.keys() else None
        self.version = int(xml_root.attrib['version']) if 'version' in xml_root.attrib.keys() else None
        self.flows = []

        self.networks = {}
        for network in xml_root.findall('./topology/networks/network'):
            network_id = int(network.attrib['id'])
            network_name = network.attrib['name'] if 'name' in xml_root.attrib.keys() else None
            network_left = int(network.attrib['left']) if 'left' in network.attrib.keys() else None
            network_top = int(network.attrib['top']) if 'top' in network.attrib.keys() else None
            self.networks[network_id] = Network(
                id = network_id,
                name = network_name,
                left = network_left,
                top = network_top
            )

        self.nodes = {}
        for node in xml_root.findall('./topology/nodes/node'):
            node_id = int(node.attrib['id'])
            node_name = node.attrib['name'] if 'name' in node.attrib.keys() else None
            node_left = node.attrib['left'] if 'left' in node.attrib.keys() else None
            node_top = node.attrib['top'] if 'top' in node.attrib.keys() else None
            self.nodes[node_id] = Node(
                id = node_id,
                name = node_name,
                left = node_left,
                top = node_top
            )
            for interface in node.findall('./interface'.format(node_id)):
                interface_id = int(interface.attrib['id'])
                interface_mac = interface.attrib['mac'] if 'mac' in interface.attrib.keys() else None
                interface_name = interface.attrib['name'] if 'name' in interface.attrib.keys() else None
                interface_type = interface.attrib['type']
                if interface_type == 'ethernet':
                    interface_network_id = int(interface.attrib['network_id']) if 'network_id' in interface.attrib.keys() else None
                    self.nodes[node_id].addInterface(id = interface_id, type = interface_type, mac = interface_mac, name = interface_name, network_id = interface_network_id)
                    self.networks[interface_network_id].addDestination(node_id = node_id, interface_id = interface_id)
                if interface_type == 'serial':
                    interface_remote_id = int(interface.attrib['remote_id']) if 'remote_id' in interface.attrib.keys() else None
                    interface_remote_if = int(interface.attrib['remote_if']) if 'remote_if' in interface.attrib.keys() else None
                    self.nodes[node_id].addInterface(id = interface_id, type = interface_type, name = interface_name, remote_id = interface_remote_id, remote_if = interface_remote_if)
                    self.flows.append({
                        'src_id': node_id,
                        'src_if': interface_id,
                        'dst_id': interface_remote_id,
                        'dst_if': interface_remote_if,
                        'type': 'serial'
                    })

        for network_id, network in self.networks.items():
            network_id = int(network_id)
            for source in network.destinations:
                for destination in network.destinations:
                    if source['node_id'] != destination['node_id']:
                        self.flows.append({
                            'src_id': source['node_id'],
                            'src_if': source['interface_id'],
                            'dst_id': destination['node_id'],
                            'dst_if': destination['interface_id'],
                            'type': 'ethernet'
                        })
            
        #textobjects
        #pictures
        #tenant
        #version
        #scripttimeout

    def open(self, username):
        max_labels = User.query.get(username).labels
        active_labels = ActiveNode.query.filter(ActiveNode.username == username).count()
        print(max_labels)
        print(active_labels)
        print("open")

    #    import xml.etree.ElementTree as ElementTree
    #    for interface in xml_root.findall('./topology/nodes/node/interface[@network_id="1"]'):
    #        interface_id = int(interface.attrib['id'])
    #        print(interface_id)
        #for node in xml_root.findall('./topology/nodes/node'):
        #    node_id = int(node.attrib['id'])
        #    for interface in node.findall('./topology/nodes/node/interface'):
        #        interface_id = int(interface.attrib['id'])
        #        interface_type = interface.attrib['type']
        #        if interface_type == 'ethernet':
        #            interface_network_id = int(interface.attrib['network_id']) if 'network_id' in interface.attrib.keys() else None
        #        if interface_type == 'serial':
        #            interface_remote_id = int(interface.attrib['remote_id']) if 'remote_id' in interface.attrib.keys() else None
        #            interface_remote_if = int(interface.attrib['remote_if']) if 'remote_if' in interface.attrib.keys() else None
        return 'ciao'


class Network:
    def __repr__(self):
        return '<Network(id={})>'.format(self.id)
    def __init__(self, id = None, name = None, left = None, top = None):
        self.id = id
        self.name = name
        self.left = left
        self.top = top
        self.destinations = []
    def addDestination(self, node_id, interface_id):
        self.destinations.append({
            'node_id': node_id,
            'interface_id': interface_id
        })

class Node:
    def __repr__(self):
        return '<Node(id={})>'.format(self.id)
    def __init__(self, id = None, name = None, left = None, top = None):
        self.id = id
        self.name = name
        self.left = left
        self.top = top
        self.interfaces = {}
        self.slots = {}
        # $flags_eth;
        # $flags_ser;
        # $config;
        # $config_data;
        # $console;
        # $cpu;
        # $delay;
        # $ethernet;
        # $ethernets = Array();
        # $firstmac;
        # $host;
        # $icon;
        # $idlepc;
        # $image;
        # $lab_id;
        # $nvram;
        # $port;
        # $ram;
        # $serial;
        # $serials = Array();
        # $slots = Array();
        # $template;
        # $tenant;
        # $type;
        # $uuid;
    def addInterface(self, id = id, type = type, mac = None, name = None, network_id = None, remote_id = None, remote_if = None):
        if type == 'ethernet': self.interfaces[id] = Ethernet(id = id, mac = mac, name = name, network_id = network_id)
        if type == 'serial': self.interfaces[id] = Serial(id = id, name = name, remote_id = remote_id, remote_if = remote_if)

class Role(db.Model):
    __tablename__ = 'roles'
    role = db.Column(db.String(255), primary_key = True)
    access_to = db.Column(db.String(255))
    can_write = db.Column(db.Boolean())
    users = db.relationship('User', secondary = roles_to_users, back_populates = 'roles')
    def __repr__(self):
        return '<Role({})>'.format(self.role)

class Roles2Users(db.Model):
    __tablename__ = 'roles_2_users'
    username = db.Column(db.String(255), db.ForeignKey('users.username'), primary_key = True)
    role = db.Column(db.String(255), db.ForeignKey('roles.role'), primary_key = True)
    def __repr__(self):
        return '<Role2User({}.{})>'.format(self.role, self.username)

class Serial:
    type = 'serial'
    def __repr__(self):
        return '<Serial(id={})>'.format(self.id)
    def __init__(self, id = None, name = None, remote_id = None, remote_if = None):
        self.remote_id = remote_id
        self.remote_if = remote_if

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(255), primary_key = True)
    password = db.Column(db.String(255))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique = True)
    labels = db.Column(db.Integer)
    roles = db.relationship('Role', secondary = roles_to_users, back_populates = 'users')
    def __repr__(self):
        return '<User({})>'.format(self.username)

def checkAuth(username, password):
    user = User.query.get(username)
    if not user:
        return False
    if user.password != hashlib.sha256(password.encode('utf-8')).hexdigest():
        return False
    return True

def checkAuthz(username, roles):
    user = User.query.get(username)
    if not user:
        return False
    for role in user.roles:
        if role.role in roles:
            return True
    return False

def checkAuthzPath(username, path, would_write = False):
    import re
    user = User.query.get(username)
    if not user:
        return False
    for role in user.roles:
        try:
            pattern = re.compile(role.access_to)
            if pattern.match(path) != None:
                if would_write and not role.can_write:
                    return False
                return True
        except Exception as err:
            return False
    return False

def addFolder():
    import json, os
    data = json.loads(flask.request.data.decode('utf-8'))
    if not 'path' in data.keys() or not 'name' in data.keys() or not isFolder(data['name']):
        flask.abort(422)
    data['path'] = os.path.join('/', data['path'])
    if not checkAuthzPath(flask.request.authorization.username, data['path'], True):
        flask.abort(403)
    if os.path.isdir('{}{}/{}'.format(PATH_LABS, data['path'], data['name'])):
        flask.abort(409)
    if not os.path.isdir('{}{}'.format(PATH_LABS, data['path'])):
        flask.abort(404)
    os.mkdir('{}{}/{}'.format(PATH_LABS, data['path'], data['name']))
    response = {
        'code': 201,
        'status': 'success',
        'message': 'Folder "{}/{}" added'.format(data['path'], data['name'])
    }
    return flask.jsonify(response), response['code']

def addUser():
    import json
    data = json.loads(flask.request.data.decode('utf-8'))
    if not 'username' in data.keys() or not 'password' in data.keys():
        flask.abort(422)
    data['password'] = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
    user = User.query.get(data['username'])
    if not user:
        flask.abort(409)
    try:
        user = User(**data)
    except Exception as err:
        flask.abort(422)
    db.session.add(user)
    db.session.commit()
    cache.set(user.username, user)
    response = {
        'code': 201,
        'status': 'success',
        'message': 'User "{}" added'.format(user.username)
    }
    return flask.jsonify(response), response['code']

def deleteFolder(folder):
    import flask, os, shutil
    if not checkAuthzPath(flask.request.authorization.username, folder, True):
        flask.abort(403)
    if folder == '/':
        flask.abort(400)
    if not os.path.isdir('{}{}'.format(PATH_LABS, folder)):
        flask.abort(404)
    shutil.rmtree('{}{}'.format(PATH_LABS, folder))
    response = {
        'code': 200,
        'status': 'success',
        'message': 'Folder "{}" deleted'.format(folder)
    }
    # TODO should update cache too
    return flask.jsonify(response), response['code']

def deleteUser(username):
    user = User.query.get(username)
    if not user:
        flask.abort(404)
    db.session.delete(user)
    db.session.commit()
    cache.delete(username)
    response = {
        'code': 200,
        'status': 'success',
        'message': 'User "{}" deleted'.format(username)
    }
    return flask.jsonify(response), response['code']

def editFolder(folder):
    import flask, json, os, shutil
    data = json.loads(flask.request.data.decode('utf-8'))
    if not checkAuthzPath(flask.request.authorization.username, folder, True) or not checkAuthzPath(flask.request.authorization.username, data['path'], True):
        flask.abort(403)
    if folder == '/' or data['path'] == '/':
        flask.abort(400)
    if not os.path.isdir('{}{}'.format(PATH_LABS, folder)) or not os.path.isdir('{}{}'.format(PATH_LABS, os.path.dirname(data['path']))):
        flask.abort(404)
    if os.path.isdir('{}{}'.format(PATH_LABS, data['path'])):
        flask.abort(409)
    shutil.move('{}{}'.format(PATH_LABS, folder), '{}{}'.format(PATH_LABS, data['path']))
    response = {
        'code': 200,
        'status': 'success',
        'message': 'Folder "{}" moved'.format(folder)
    }
    # TODO should update cache too
    return flask.jsonify(response), response['code']

def editUser(username):
    import json
    data = json.loads(flask.request.data.decode('utf-8'))
    if 'username' in data.keys():
        flask.abort(422)
    if 'password' in data.keys():
        data['password'] = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
    user = User.query.get(username)
    if not user:
        flask.abort(404)
    for key, value in data.items():
        if not hasattr(user, key):
            flask.abort(422)
        setattr(user, key, value)
    db.session.commit()
    response = {
        'code': 200,
        'status': 'success',
        'message': 'User "{}" modified'.format(username)
    }
    return flask.jsonify(response), response['code']

def getFolder(folder):
    import flask, os
    if not checkAuthzPath(flask.request.authorization.username, folder):
        flask.abort(403)
    if not os.path.isdir('{}{}'.format(PATH_LABS, folder)):
        flask.abort(404)
    response = {
        'code': 200,
        'status': 'success',
        'data': {
            'folders': {},
            'labs': {}
        },
        'message': 'Folder "{}" displayed'.format(folder)
    }
    labs = Lab.query.filter(Lab.path == folder)
    if folder == '/':
        for dir in os.walk('{}{}'.format(PATH_LABS, folder)).__next__()[1]:
            response['data']['folders'][dir] = '/{}'.format(dir)
        for lab in labs:
            response['data']['labs'][lab.name] = '/{}'.format(lab.filename)
    else:
        response['data']['folders']['..'] = os.path.dirname(folder)
        for dir in os.walk('{}{}'.format(PATH_LABS, folder)).__next__()[1]:
            response['data']['folders'][dir] = '{}/{}'.format(folder, dir)
        for lab in labs:
            response['data']['labs'][lab.name] = '{}/{}'.format(lab.path, lab.filename)
    return flask.jsonify(response), response['code']

def getUsers(username = None):
    response = {
        'code': 200,
        'status': 'success'
    }
    if username == None:
        response['message'] = 'All users displayed'
        response['data'] = {}
        for user in User.query:
            response['data'][user.username] = printUser(user)
    else:
        response['message'] = 'User "{}" displayed'.format(username)
        user = User.query.get(username)
        if not user:
            flask.abort(404)
        response['data'] = printUser(user)
    return flask.jsonify(response), response['code']

def isFolder(folder):
    import re
    pattern = re.compile(r'^[A-Za-z0-9 +]+$')
    if pattern.match(folder) != None:
        return True
    return False

def manageLab(path, method):
    import os, re
    username = flask.request.authorization.username
    can_read = checkAuthzPath(username, path)
    can_write = checkAuthzPath(username, path, True)

    if not can_read:
        flask.abort(403)

    pattern = re.match(r'^(.+)\.{}(/([a-z]+))?(/*(all|[0-9]*))?$'.format(LAB_EXTENSION), path, re.M|re.I)
    if pattern:
        lab_filename = os.path.basename('{}.{}'.format(pattern.group(1), LAB_EXTENSION))
        lab_path = os.path.dirname('{}.{}'.format(pattern.group(1), LAB_EXTENSION))
        lab_object = pattern.group(3)
        object_id = pattern.group(5)
    else:
        flask.abort(400)

    lab = cache.get('{}/{}'.format(lab_path, lab_filename))
    if not lab:
        # Cache is empty
        labs = Lab.query.filter(Lab.path == lab_path, Lab.filename == lab_filename)
        if labs.count() == 0:
            flask.abort(404)
        lab = labs.one()
        #cache.set('{}/{}'.format(lab_path, lab_filename), lab) # TODO enable for production

    if method == 'CLOSE':
        print(method)
    elif method == 'DELETE':
        print(method)
    elif method == 'GET':
        if lab_object == None:
            # Print lab info
            response = {
                'code': 200,
                'status': 'success',
                'message': 'Lab "{}/{}" displayed'.format(lab.path, lab.filename),
                'data': printLab(lab)
            }
            return flask.jsonify(response), response['code']
        elif lab_object == 'networks':
            # Print networks
            response = {
                'code': 200,
                'status': 'success',
            }
            if object_id == '':
                response['message'] = 'Lab "{}/{}": all networks displayed'.format(lab.path, lab.filename)
                response['data'] = {}
                for network_id, network in lab.networks.items():
                    network_id = int(network_id)
                    response['data'][network_id] = printNetwork(network)
            else:
                if not object_id in lab.networks.keys():
                    flask.abort(404)
                response['message'] = 'Lab "{}/{}": network "{}" displayed'.format(lab.path, lab.filename, object_id)
                response['data'] = printNetwork(lab.networks[object_id])
            return flask.jsonify(response), response['code']
        elif lab_object == 'nodes':
            # Print nodes
            response = {
                'code': 200,
                'status': 'success',
            }
            if object_id == '':
                response['message'] = 'Lab "{}/{}": all nodes displayed'.format(lab.path, lab.filename)
                response['data'] = {}
                for node_id, node in lab.nodes.items():
                    node_id = int(node_id)
                    response['data'][node_id] = printNode(node)
            else:
                if not object_id in lab.nodes.keys():
                    flask.abort(404)
                response['message'] = 'Lab "{}/{}": node "{}" displayed'.format(lab.path, lab.filename, object_id)
                response['data'] = printNode(lab.nodes[object_id])
            return flask.jsonify(response), response['code']
        else:
            raise Exception('Object not recognized')
    elif method == 'OPEN':
        return openLab(lab, username)
    elif method == 'POST':
        print(method)
    elif method == 'PUT':
        print(method)
    elif method == 'START':
        print(method)
    elif method == 'STOP':
        print(method)
    raise Exception('Method not defined')

def openLab(lab, username):
    return lab.open(username = username)

    controller_id = 0 # TODO

    # Converting BaseQuery to dict
    active_nodes = {}
    for active_node in ActiveNode.query.filter(ActiveNode.lab_id == lab.id, ActiveNode.username == username):
        active_nodes[active_node.node_id] = active_node

    # Check if each node has a label
    for node_id, node in lab.nodes.items():
        node_id = int(node_id)
        if node_id not in active_nodes:
            # Add each node as active_node
            active_node = ActiveNode(username = username, lab_id = lab.id, node_id = node_id, state = 'off', controller = controller_id)
            db.session.add(active_node)
            db.session.commit() # TODO should do a single commit

    # Check for unused labels (deleted nodes)
    for active_node_id, active_node in active_nodes.items():
        active_node_id = int(active_node_id)
        if active_node_id not in lab.nodes.items():
            # Delete unused label
            db.session.delete(active_node)
            db.session.commit() # TODO should do a single commit
            for label in ActiveTopology.query.filter((ActiveTopology.src_id == active_node.label) | (ActiveTopology.dst_id == active_node.label)):
                db.session.delete(label)
                db.session.commit() # TODO should do a single commit

    # Populate active_topologies
    for src_node_id, src_node in lab.nodes.items():
        src_node_id = int(src_node_id)
        # For each node
        src_node_id = int(src_node_id)
        for src_node_if_id, src_node_if in src_node.interfaces.items():
            src_node_if_id = int(src_node_if_id)
            # For each Ethernet interface
            if src_node_if.type == 'ethernet' and src_node_if.network_id:
                for dst_node_id, dst_node in lab.nodes.items():
                    dst_node_id = int(dst_node_id)
                    # Find destination node
                    if src_node_id != dst_node_id:
                        for dst_node_if_id, dst_node_if in dst_node.interfaces.items():
                            if src_node_if.network_id == dst_node_if.network_id:
                                active_topologies = ActiveTopology.query.filter((ActiveTopology.src_id == src_node_id) & (ActiveTopology.src_if == src_node_if_id) & (ActiveTopology.dst_id == dst_node_id) & (ActiveTopology.dst_if == dst_node_if_id))
                                if active_topologies.count() == 0:
                                    active_topology = ActiveTopology(src_id = src_node_id, src_if = src_node_if_id, dst_id = dst_node_id, dst_if = dst_node_if_id)
                                    db.session.add(active_topology)
                                    db.session.commit() # TODO should commit once
                                    # dainok




    # Fields: controller_id 1 byte, label 4 byte, interface 1 byte
    response = {
        'code': 200,
        'status': 'success',
    }
    return flask.jsonify(response), response['code']

def printLab(lab):
    output = {}
    if lab.author: output['author'] = lab.author
    if lab.body: output['body'] = lab.body
    if lab.description: output['description'] = lab.description
    output['filename'] = lab.filename
    output['id'] = lab.id
    output['name'] = lab.name
    if lab.version: output['version'] = lab.version
    return output

def printNetwork(network):
    output = {}
    output['id'] = network.id
    if network.name: output['name'] = network.name
    if network.left: output['left'] = network.left
    if network.top: output['top'] = network.top
    return output

def printNode(node):
    output = {}
    output['id'] = node.id
    if node.name: output['name'] = node.name
    if node.left: output['left'] = node.left
    if node.top: output['top'] = node.top
    if len(node.interfaces) > 0:
        output['interfaces'] = {}
        for interface_id, interface in node.interfaces.items():
            interface_id = int(interface_id)
            output['interfaces'][interface_id] = {
                'id': interface.id,
                'type': interface.type
            }
            if interface.name: output['interfaces'][interface_id]['name'] = interface.name
            if interface.mac: output['interfaces'][interface_id]['mac'] = interface.mac
            if interface.type == 'ethernet' and interface.network_id: output['interfaces'][interface_id]['network_id'] = interface.network_id
            if interface.type == 'serial' and interface.remote_id and interface.remote_if:
                 output['interfaces'][interface_id]['remote_id'] = interface.remote_id
                 output['interfaces'][interface_id]['remote_if'] = interface.remote_if
    return output

def printUser(user):
    output = {}
    if user.email: output['email'] = user.email
    if user.labels: output['labels'] = user.labels
    if user.name: output['name'] = user.name
    output['username'] = user.username
    return output

def refreshDb():
    #TODO: after folder delete should invalidate cache
    import fnmatch, os, re
    import xml.etree.ElementTree as ElementTree
    labs = {}
    for root, dirnames, filenames in os.walk(PATH_LABS):
        for filename in fnmatch.filter(filenames, '*.{}'.format(LAB_EXTENSION)):
            lab_filename = (os.path.join(root, filename))
            xml = ElementTree.parse(lab_filename)
            xml_root = xml.getroot()
            data = {
                'id': xml_root.attrib['id'],
                'name': xml_root.attrib['name'],
                'filename': os.path.basename(lab_filename),
                'path': os.path.dirname(lab_filename).replace(PATH_LABS, '', 1)
            }
            # Fix empty path from dirname + replace
            if data['path'] == '':
                data['path'] = '/'
            labs[xml_root.attrib['id']] = Lab(**data)
    # Removing nonexistent labs from DB
    labs_from_db = Lab.query.all()
    for lab_from_db in labs_from_db:
        if lab_from_db.id not in labs:
            # Delete the lab
            db.session.delete(lab_from_db)
            # Delete the active nodes
            db.session.add_all(ActiveNode.query.filter(ActiveNode.lab_id == lab_from_db.id))
            # Delete the active topologies
            db.session.add_all(ActiveTopology.query.filter(ActiveTopology.lab_id == lab_from_db.id))
            db.session.commit() # TODO should use a single commit, but got an error
            # Delete the cache
            cache.delete('{}/{}'.format(lab_from_db.path, lab_from_db.filename))
    # Checking missing labs to DB
    for lab_id, lab in labs.items():
        commit = False
        lab_from_db = Lab.query.get(lab.id)
        if not lab_from_db:
            # Lab need to be added
            commit = True
            db.session.add(lab)
        else:
            # Lab already exist, check name and path
            commit = False
            if lab.name != lab_from_db.name:
                lab_from_db.update({'name': lab.name})
                commit = True
            if lab.filename != lab_from_db.filename:
                lab_from_db.update({'filename': lab.filename})
                commit = True
            if lab.path != lab_from_db.path:
                lab_from_db.update({'path': lab.path})
                commit = True
        if commit:
            # TODO should use a single commit (not one for each for), but got an error
            db.session.commit()
    response = {
        'code': 200,
        'status': 'success',
        'message': 'Database refreshed'
    }
    return flask.jsonify(response), response['code']

def requiresAuth(f):
    import flask, functools
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = flask.request.authorization
        if not auth or not checkAuth(auth.username, auth.password):
            flask.abort(401)
        return f(*args, **kwargs)
    return decorated

def requiresRoles(*roles):
    import flask, functools
    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            auth = flask.request.authorization
            if not checkAuthz(auth.username, roles):
                flask.abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper
