from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__, static_folder=os.path.abspath('/Users/NolanRoth/Desktop/ProjectWebsite'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rankings.db'
app.config['SECRET_KEY'] = 'ee0442debd6e5574666cd67a'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"
from website import routes
