from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
logging.basicConfig(level=logging.WARNING)

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///LizardCatalog.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['CLEARDB_DATABASE_URL']
app.config[' SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# Initialize third party modules
db = SQLAlchemy(app)

# Create global session for Flask-SQLAlchemy
session = db.session

# Import modules that contain routes.  Must be imported after db, moment, and
# session are initialized because those variables are used in these imports.
# If placed at the top of the init file, everything would crash due to circular
# dependency chain
import pkg.databaseSetup
import pkg.main
import pkg.APIEndpoints
import pkg.oauth
