#!/usr/bin/env python3

import flask, flask_sqlalchemy

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = flask_sqlalchemy.SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True)
    password = db.Column(db.String(80))
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique = True)
    label_start = db.Column(db.Integer)
    label_end = db.Column(db.Integer)

    def __repr__(self):
        return '<User(id={})>'.format(self.username)

class Lab(db.Model):
    __tablename__ = 'labs'

    id = db.Column(db.String(20), primary_key = True)
    name = db.Column(db.String(20))
    path = db.Column(db.String(20))

    def __repr__(self):
        return '<Lab(id={})>'.format(id)

class ActiveNode(db.Model):
    __tablename__ = 'active_nodes'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lab_id = db.Column(db.String, db.ForeignKey('labs.id'))
    node_id = db.Column(db.Integer)
    iface_id = db.Column(db.Integer)
    label = db.Column(db.Integer, primary_key = True)
    state = db.Column(db.String(10))
    controller = db.Column(db.String(100))

    def __repr__(self):
        return '<Node(label={})>'.format(label)

class ActiveTopology(db.Model):
    __tablename__ = 'active_topologies'

    src = db.Column(db.Integer, db.ForeignKey('active_nodes.label'), primary_key = True)
    dst = db.Column(db.Integer, db.ForeignKey('active_nodes.label'), primary_key = True)

    def __repr__(self):
        return '<Topology(src={}, dst={}>'.format(src, dst)


if __name__ == '__main__':
    # http://flask-sqlalchemy.pocoo.org/2.1/quickstart/#a-minimal-application
    # from yourapplication import db
    # from yourapplication import User

    db.create_all()
    admin = User(username = 'admin', name = 'Administrator', email = 'admininistrator@example.com', label_start = 0, label_end = 199)
    andrea = User(username = 'andrea', name = 'Andrea Dainese', email = 'andrea.dainese@gmail.com', label_start = 200, label_end = 399)
    users = [ ]
    #users.append(admin)
    #users.append(andrea)
    
    for user in User.query.filter(User.username == 'admin'):
        print("CIAO")
        print(user.name)

    #print(db.session.query(User.id == 'admin'))
    #if admin not in User.query(User.id == 'admin'):
    #    print("adding admin")
    #    users.append(admin)
    #if andrea not in User.query.all():
    #    users.append(andrea)

    for user in users:
        db.session.add(user)
    db.session.commit()

    #print(User.query.all())
    #for user in User.query.all():
    #    print(user.username)



#import MySQLdb as mdb
#con = mdb.connect(self.db_host, self.db_user, self.db_password, self.db)
#con.set_character_set('utf8')
#
#from locale import setlocale
#setlocale(locale.LC_ALL, "nb_NO.utf8")
#

