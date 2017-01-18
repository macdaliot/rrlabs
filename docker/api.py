#!/usr/bin/env python3
""" API """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

import flask, flask_sqlalchemy, functools, logging
from api_modules import *

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
    response = {
        'code': 401,
        'status': 'unauthorized',
        'message': str(err)
    }
    return flask.jsonify(response), response['code']

@app.errorhandler(403)
def http_403(err):
    response = {
        'code': 401,
        'status': 'forbidden',
        'message': str(err)
    }
    return flask.jsonify(response), response['code']

@app.errorhandler(404)
def http_404(err):
    response = {
        'code': 404,
        'status': 'fail',
        'message': str(err)
    }
    return flask.jsonify(response), response['code']

@app.errorhandler(405)
def http_405(err):
    response = {
        'code': 405,
        'status': 'fail',
        'message': str(err)
    }
    return flask.jsonify(response), response['code']

@app.errorhandler(409)
def http_409(err):
    response = {
        'code': 409,
        'status': 'fail',
        'message': str(err)
    }
    return flask.jsonify(response), response['code']

#@app.errorhandler(Exception)
def http_500(err):
    response = {
        'code': 500,
        'status': 'error',
        'message': str(err)
    }
    logging.error(err)
    return flask.jsonify(response), response['code']

# curl -s -D- -u admin:admin -X GET http://127.0.0.1:5000/api/users
# curl -s -D- -u admin:admin -X POST -d '{"name":"andrea","email":"andrea.dainese@example.com","username":"andrea","password":"andrea"}' -H 'Content-type: application/json' http://127.0.0.1:5000/api/users
@app.route('/api/users', methods = ['GET', 'POST'])
@requiresAuth
@requiresRoles('admin')
def apiUsers(username = None):
    if flask.request.method == 'GET':
        return getUsers()
    if flask.request.method == 'POST':
        return addUser()

# curl -s -D- -u admin:admin -X GET http://127.0.0.1:5000/api/users/admin
@app.route('/api/users/<username>', methods = ['GET'])
@requiresAuth
@requiresRoles('admin')
def apiUsersUsername(username):
    return getUsers(username)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000, debug = True)

