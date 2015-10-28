
''' 
SQLAlchemy database
'''
from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
import os.path
from datetime import datetime
import sqlite3

basedir = os.path.abspath ( os.path.dirname(__file__) )

app = Flask ( __name__ )
app.config [ 'SQLALCHEMY_DATABASE_URI' ] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config [ 'SQLALCHEMY_COMMIT_ON_TEARDOWN' ] = True

db = SQLAlchemy ( app )


class Access ( db.Model ):
	__tablename__ = 'access'
	id = db.Column ( db.Integer, primary_key=True )
	ip = db.Column ( db.String ( 64 ), unique = False, index = False )
	time = db.Column ( db.DateTime )
	user_id = db.Column ( db.Integer, db.ForeignKey('users.id') )
	def __repr__ ( self ):
		return '<Access %r>' % self.id

class User ( db.Model ):
    __tablename__ = 'users'
    id = db.Column ( db.Integer, primary_key = True )
    email = db.Column ( db.String( 64 ), unique = False, index = True ) 
    license = db.Column ( db.String( 64 ), unique = True, index = True )
    active = db.Column ( db.Boolean )
    creationtime = db.Column ( db.DateTime )
    def __repr__ ( self ):
        return '<User ID %r Email %r>' % ( self.id, self.email )

class IPN ( db.Model ):
    __tablename__ = 'ipn'
    id = db.Column ( db.Integer, primary_key = True )
    payer_email = db.Column ( db.String( 64 ), unique = False, index = True ) 
    txn_id = db.Column ( db.String( 20 ), unique = True, index = True ) 
    creationtime = db.Column ( db.DateTime )
    def __repr__ ( self ):
        return '<User ID %r Email %r>' % ( self.id, self.payer_email )

class Release ( db.Model ):
	__tablename__ = "release"
	id = db.Column ( db.Integer, primary_key = True )
	time = db.Column ( db.DateTime )
	build = db.Column ( db.String( 16 ), unique = False, index = False ) 
	feature = db.Column ( db.String( 256 ), unique = False, index = False ) 
	url = db.Column ( db.String( 256 ), unique = False, index = False ) 
	def __repr__ ( self ):
		return '<Release ID %r Build %r>' % ( self.id, self.build )

def init ():
	db.drop_all ()
	db.create_all ()
	

