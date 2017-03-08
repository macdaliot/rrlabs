#!/usr/bin/env python3
""" API modules """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

DEFAULT_API_USERNAME = 'admin'
DEFAULT_API_PASSWORD = 'eve'
DB_USERNAME = 'root'
DB_PASSWORD = 'eve-ng'
DB_HOST = '127.0.0.1'
DB_NAME = 'eve'
PATH_LABS = '/opt/unetlab/labs'
LAB_EXTENSION = 'unl'

import flask, flask_sqlalchemy, functools, hashlib, logging

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/{}'.format(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME)
db = flask_sqlalchemy.SQLAlchemy(app)

roles_to_users = db.Table(
    'roles_to_users',
    db.Column('role', db.String(255), db.ForeignKey('roles.role')),
    db.Column('username', db.String(255), db.ForeignKey('users.username')),
)

class ActiveNode(db.Model):
    __tablename__ = 'active_nodes'
    user_id = db.Column(db.String, db.ForeignKey('users.username'))
    lab_id = db.Column(db.String, db.ForeignKey('labs.id'))
    node_id = db.Column(db.Integer)
    iface_id = db.Column(db.Integer)
    label = db.Column(db.Integer, primary_key = True)
    state = db.Column(db.String(255))
    controller = db.Column(db.String(255))
    def __repr__(self):
        return '<Node(label={})>'.format(label)

class ActiveTopology(db.Model):
    __tablename__ = 'active_topologies'
    src = db.Column(db.Integer, db.ForeignKey('active_nodes.label'), primary_key = True)
    dst = db.Column(db.Integer, db.ForeignKey('active_nodes.label'), primary_key = True)
    def __repr__(self):
        return '<Topology(src={}, dst={}>'.format(src, dst)

class Lab(db.Model):
    __tablename__ = 'labs'
    id = db.Column(db.String(255), primary_key = True)
    name = db.Column(db.String(255))
    filename = db.Column(db.String(255))
    path = db.Column(db.String(255))
    def __repr__(self):
        return '<Lab(id={})>'.format(id)
    @flask_sqlalchemy.orm.reconstructor
    def init_on_load(self):
        import xml.etree.ElementTree as ElementTree
        xml = ElementTree.parse('{}{}/{}'.format(PATH_LABS, self.path, self.filename))
        xml_root = xml.getroot()
        self.author = xml_root.attrib['author'] if 'author' in xml_root.attrib.keys() else ''
        self.body = xml_root.attrib['body'] if 'body' in xml_root.attrib.keys() else ''
        self.description = xml_root.attrib['description'] if 'description' in xml_root.attrib.keys() else ''
        self.version = int(xml_root.attrib['version']) if 'version' in xml_root.attrib.keys() else 0

        self.networks = {}
        for network in xml_root.findall('./topology/networks/network'):
            network_id = network.attrib['id']
            network_name = network.attrib['name'] if 'name' in xml_root.attrib.keys() else ''
            network_left = network.attrib['left'] if 'left' in xml_root.attrib.keys() else 0
            network_top = network.attrib['top'] if 'top' in xml_root.attrib.keys() else 0
            self.networks[network_id] = Network(
                id = network_id,
                name = network_name,
                left = network_left,
                top = network_top
            )

        self.nodes = {}
        for node in xml_root.findall('./topology/nodes/node'):
            node_id = node.attrib['id']
            node_name = node.attrib['name'] if 'name' in xml_root.attrib.keys() else ''
            node_left = node.attrib['left'] if 'left' in xml_root.attrib.keys() else 0
            node_top = node.attrib['top'] if 'top' in xml_root.attrib.keys() else 0
            self.nodes[node_id] = Node(
                id = node_id,
                name = node_name,
                left = node_left,
                top = node_top
            )
        #nodes
        #textobjects
        #pictures
        #tenant
        #version
        #scripttimeout
    #dainoke#

class Network:
    def __init__(self, id = None, name = '', left = 0, top = 0):
        self.id = id
        self.name = name
        self.left = left
        self.top = top

class Node:
    def __init__(self, id = None, name = '', left = 0, top = 0):
        self.id = id
        self.name = name
        self.left = left
        self.top = top

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

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(255), primary_key = True)
    password = db.Column(db.String(255))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique = True)
    label_start = db.Column(db.Integer)
    label_end = db.Column(db.Integer)
    roles = db.relationship('Role', secondary = roles_to_users, back_populates = 'users')
    def __repr__(self):
        return '<User({})>'.format(self.username)

def checkAuth(username, password):
    users = User.query.filter(User.username == username)
    if users.count() != 1:
        return False
    if users.one().password != hashlib.sha256(password.encode('utf-8')).hexdigest():
        return False
    return True

def checkAuthz(username, roles):
    users = User.query.filter(User.username == username)
    if users.count() != 1:
        return False
    for role in users.first().roles:
        if role.role in roles:
            return True
    return False

def checkAuthzPath(username, path, would_write = False):
    import re
    users = User.query.filter(User.username == username)
    if users.count() != 1:
        return False
    for role in users.first().roles:
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
    users = User.query.filter(User.username == data['username'])
    if users.count() != 0:
        flask.abort(409)
    try:
        user = User(**data)
    except Exception as err:
        flask.abort(422)
    db.session.add(user)
    db.session.commit()
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
    user = User.query.filter(User.username == username)
    if user.count() == 0:
        flask.abort(404)
    db.session.delete(user.first())
    db.session.commit()
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
    users = User.query.filter(User.username == username)
    if users.count() == 0:
        flask.abort(404)
    user = users.first()
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
        users = User.query.filter(User.username == username)
        if users.count() == 0:
            flask.abort(404)
        response['data'] = printUser(users.one())
    return flask.jsonify(response), response['code']

def isFolder(folder):
    import re
    pattern = re.compile(r'^[A-Za-z0-9 +]+$')
    if pattern.match(folder) != None:
        return True
    return False

def manageLab(path, method):
    import os, re
    can_read = checkAuthzPath(flask.request.authorization.username, path)
    can_write = checkAuthzPath(flask.request.authorization.username, path, True)

    pattern = re.match(r'^(.+)\.{}(/([a-z]+))?(/*(all|[0-9]*))?$'.format(LAB_EXTENSION), path, re.M|re.I)
    if pattern:
        lab_filename = os.path.basename('{}.{}'.format(pattern.group(1), LAB_EXTENSION))
        lab_path = os.path.dirname('{}.{}'.format(pattern.group(1), LAB_EXTENSION))
        lab_object = pattern.group(3)
        object_id = pattern.group(5)
    else:
        flask.abort(400)

    labs = Lab.query.filter(Lab.path == lab_path, Lab.filename == lab_filename)
    if labs.count() == 0:
        flask.abort(404)
    lab = labs.one()

    if method == 'DELETE':
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
                    response['data'][node_id] = printNode(node)
            else:
                if not object_id in lab.nodes.keys():
                    flask.abort(404)
                response['message'] = 'Lab "{}/{}": node "{}" displayed'.format(lab.path, lab.filename, object_id)
                response['data'] = printNode(lab.nodes[object_id])
            return flask.jsonify(response), response['code']
        elif lab_object == 'open':
            print('open')
        elif lab_object == 'close':
            print('close')
    elif method == 'POST':
        print(method)
    elif method == 'PUT':
        print(method)
    elif method == 'START':
        print(method)
    elif method == 'STOP':
        print(method)

    print(lab_filename)
    print(lab_object)
    print(object_id)
    #print(object_action)

    # Inner Label: destination docker instance
    # Outer Label: destination docker server


    #print(path)
    #print(method)
    #if not checkAuthzPath(flask.request.authorization.username, data['path'], True):
    return "ciao"

def printLab(lab):
    return {
        'author': lab.author,
        'body': lab.body,
        'description': lab.description,
        'filename': lab.filename,
        'id': lab.id,
        'name': lab.name,
        'version': lab.version
    }

def printNetwork(network):
    return {
        'id': network.id,
        'name': network.name,
        'left': network.left,
        'top': network.top
    }

def printNode(node):
    return {
        'id': node.id,
        'name': node.name,
        'left': node.left,
        'top': node.top
    }

def printUser(user):
    return {
        'email': user.email,
        'name': user.name,
        'username': user.username,
        'label_start': user.label_start,
        'label_end': user.label_end
    }

def refreshDb():
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
            db.session.delete(lab_from_db)
            # TODO should use a single commit, but got an error
            db.session.commit()
    # Checking missing labs to DB
    for lab_id, lab in labs.items():
        commit = False
        lab_from_db = Lab.query.filter(Lab.id == lab.id)
        if lab_from_db.count() == 0:
            # Lab need to be added
            commit = True
            db.session.add(lab)
        else:
            # Lab already exist, check name and path
            commit = False
            if lab.name != lab_from_db.first().name:
                lab_from_db.update({'name': lab.name})
                commit = True
            if lab.filename != lab_from_db.first().filename:
                lab_from_db.update({'filename': lab.filename})
                commit = True
            if lab.path != lab_from_db.first().path:
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
