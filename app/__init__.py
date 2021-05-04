from flask import Flask, session
import os
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
UPLOAD_FOLDER = os.path.abspath("./app/static/uploads/")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "Python application"

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'literature_review'

mysql = MySQL(app)

@app.before_request
def session_management():
  session.permanent = True
from app import routes