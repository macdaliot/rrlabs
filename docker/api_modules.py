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

import flask, flask_sqlalchemy, functools, hashlib, logging

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/{}'.format(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME)
db = flask_sqlalchemy.SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(255), primary_key = True)
    password = db.Column(db.String(255))
    #roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique = True)
    label_start = db.Column(db.Integer)
    label_end = db.Column(db.Integer)
    def __repr__(self):
        return '<User({})>'.format(self.username)

#class Role(db.Model):
#    __tablename__ = 'roles'
#
#    id = db.Column(db.Integer(), primary_key = True)
#    name = db.Column(db.String(50), unique = True)
#
#    def __repr__(self):
#        return '<Role({})>'.format(self.name)

#class UserRoles(db.Model):


class Lab(db.Model):
    __tablename__ = 'labs'
    id = db.Column(db.String(255), primary_key = True)
    name = db.Column(db.String(255))
    path = db.Column(db.String(255))
    def __repr__(self):
        return '<Lab(id={})>'.format(id)

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

def checkAuth(username, password):
    users = User.query.filter(User.username == username)
    if users.count() != 1:
        return False
    if users.one().password != hashlib.sha256(password.encode('utf-8')).hexdigest():
        return False
    return True

def checkAuthz(username, roles):
    if username == 'admin':
        return True
    return False

def addUser():
    import json
    data = json.loads(flask.request.data.decode('utf-8'))
    user = User(**data)
    user.password = hashlib.sha256(user.password.encode('utf-8')).hexdigest():
    users = User.query.filter(User.username == user.username)
    if users.count() != 0:
        flask.abort(409)
    db.session.add(user)
    db.session.commit()
    response = {
        'code': 201,
        'status': 'success',
        'message': 'User added'
    }
    return flask.jsonify(response), response['code']

def getUser(username):
    return getUsers(username)

def getUsers(username = None):
    response = {}
    if username == None:
        response['message'] = 'All users listed'
        users = User.query
    else:
        response['message'] = 'User listed'
        users = User.query.filter(User.username == username)
    if users.count() == 0:
        flask.abort(404)
    else:
        response['code'] = 200
        response['status'] = 'success'
        response['data'] = {}
    for user in users:
        response['data'][user.username] = {
            'email': user.email,
            'name': user.name,
            'username': user.username,
            'label_start': user.label_start,
            'label_end': user.label_end
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
