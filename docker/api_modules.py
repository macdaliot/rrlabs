#!/usr/bin/env python3
""" API modules """
__author__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__copyright__ = 'Andrea Dainese <andrea.dainese@gmail.com>'
__license__ = 'https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode'
__revision__ = '20170105'

def check_auth(username, password):
    if username == 'admin' and password == 'admin':
        return True
    else:
        return False

def check_authz(username, roles):
    if username == 'admin':
        return True
    return False

def requires_auth(f):
    import flask, functools
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = flask.request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            flask.abort(401)
        return f(*args, **kwargs)
    return decorated

def requires_roles(*roles):
    import flask, functools
    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            auth = flask.request.authorization
            print(auth)
            if not check_authz(auth.username, roles):
                flask.abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper

