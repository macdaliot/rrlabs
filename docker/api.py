#!/usr/bin/env python3
""" API """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

import flask, flask_sqlalchemy, functools
from api_modules import *

DEFAULT_API_USERNAME = 'admin'
DEFAULT_API_PASSWORD = 'eve'
DB_USERNAME = 'root'
DB_PASSWORD = 'eve-ng'
DB_HOST = '127.0.0.1'
DB_NAME = 'eve'

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/{}'.format(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME)
db = flask_sqlalchemy.SQLAlchemy(app)

#http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api
#http://flask.pocoo.org/snippets/83/
#http://www.flaskapi.org/api-guide/status-codes/
#success for 20x HTTP codes;
#unauthorized for 401 HTTP code, meaning that user should login;
#forbidden for 403 HTTP code, meaning that user does not have enough privileges;
#fail for other 40x HTTP codes;
#error for 50x HTTP codes.
#http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#common-filter-operators
# https://flask-httpauth.readthedocs.io/en/latest/
#https://pythonhosted.org/Flask-User/authorization.html#login-required
#GET /tickets - Retrieves a list of tickets
#GET /tickets/12 - Retrieves a specific ticket
#POST /tickets - Creates a new ticket
#PUT /tickets/12 - Updates ticket #12
#PATCH /tickets/12 - Partially updates ticket #12
#DELETE /tickets/12 - Deletes ticket #12
# ERrors:
# 401 you're not authenticated
# 403 you're authenticated but not authorized

@app.errorhandler(401)
def http_401(err):
    output = {}
    output['code'] = 401
    output['status'] = 'unauthorized'
    output['message'] = str(err)
    return flask.jsonify(output), output['code']

@app.errorhandler(403)
def http_403(err):
    output = {}
    output['code'] = 401
    output['status'] = 'forbidden'
    output['message'] = str(err)
    return flask.jsonify(output), output['code']

@app.errorhandler(404)
def http_404(err):
    output = {}
    output['code'] = 404
    output['status'] = 'fail'
    output['message'] = str(err)
    return flask.jsonify(output), output['code']

@app.errorhandler(Exception)
def http_500(err):
    output = {}
    output['code'] = 500
    output['status'] = 'error'
    output['message'] = str(err)
    return flask.jsonify(output), output['code']

@app.route('/api/users', methods=['GET'])
@requires_auth
@requires_roles('admin')
def getUsers(username = None):
    output = {}
    if username == None:
        output['message'] = 'All users listed'
        users = User.query
    else:
        output['message'] = 'User listed'
        users = User.query.filter(User.username == username)
    if users.count() == 0:
        flask.abort(404)
    else:
        output['code'] = 200
        output['status'] = 'success'
        output['data'] = {}
    for user in users:
        output['data'][user.username] = {
            'email': user.email,
            'name': user.name,
            'username': user.username,
            'label_start': user.label_start,
            'label_end': user.label_end
        }
    return flask.jsonify(output), output['code']

@app.route('/api/users/<username>', methods=['GET'])
@requires_auth
@requires_roles('admin')
def getUser(username):
    return getUsers(username)











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


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000, debug = True)
    # http://flask-sqlalchemy.pocoo.org/2.1/quickstart/#a-minimal-application
    # from yourapplication import db
    # from yourapplication import User

    #db.create_all()
    #admin = User(username = 'admin', password = 'admin', name = 'Administrator', email = 'admininistrator@example.com', label_start = 0, label_end = 199)
    #andrea = User(username = 'andrea', password = 'andrea', name = 'Andrea Dainese', email = 'andrea.dainese@gmail.com', label_start = 200, label_end = 399)
    #users = [ ]
    #users.append(admin)
    #users.append(andrea)
    
    #for user in User.query.filter(User.username == 'admin'):
    #    print("CIAO")
    #    print(user.name)

    #print(db.session.query(User.id == 'admin'))
    #if admin not in User.query(User.id == 'admin'):
    #    print("adding admin")
    #    users.append(admin)
    #if andrea not in User.query.all():
    #    users.append(andrea)

    #for user in users:
    #    db.session.add(user)
    #db.session.commit()

    #print(User.query.all())
    #for user in User.query.all():
    #    print(user.username)



#import MySQLdb as mdb
#con = mdb.connect(self.db_host, self.db_user, self.db_password, self.db)
#con.set_character_set('utf8')
#
#from locale import setlocale
#setlocale(locale.LC_ALL, "nb_NO.utf8")

