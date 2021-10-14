from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__, static_folder=os.path.abspath('/Users/NolanRoth/Desktop/ProjectWebsite'))
app.jinja_options['extensions'].append('jinja2.ext.do')

# change this to dev to use development database and prod to use production database
is_prod = os.environ.get('IS_HEROKU', None)

if is_prod:
	app.debug = False
	app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('PROD_DATABASE_URI')
	app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
else:
	app.debug = True
	import config
	app.config['SQLALCHEMY_DATABASE_URI'] = config.dev_database_uri
	app.config['SECRET_KEY'] = config.app_secret_key

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"

# Comment out when you want to run build_database.py or you will get errors
from website import routes