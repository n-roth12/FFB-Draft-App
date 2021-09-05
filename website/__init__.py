from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__, static_folder=os.path.abspath('/Users/NolanRoth/Desktop/ProjectWebsite'))
app.config['SECRET_KEY'] = 'ee0442debd6e5574666cd67a'
app.jinja_options['extensions'].append('jinja2.ext.do')

# change this to dev to use development database and prod to use production database
ENV = 'prod'

if ENV == 'dev':
	app.debug = True
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:%40Vcs39706@localhost/rankings'
else:
	app.debug = False
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ejwlsaknequdfu:a354bde5759165e426c0c8d2cc94fd12fb29bc9b65ed4f5eda9b6027c9377058@ec2-44-194-145-230.compute-1.amazonaws.com:5432/d8sj9c085m0joh'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"

# Comment out when you want to run build_database.py or you will get errors
from website import routes