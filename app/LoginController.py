#!/usr/bin/python
from flask import render_template, session, request, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
from app import app
import bcrypt
import re
from app import mysql

#########################
# Métodos
#########################


def login():
    if session.get('loggedin') is not None:
        return redirect(url_for('home'))
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            #Convertir de String a byte contraseña ingresada
            password = str.encode(password)
            #Convertir de String a byte contraseña guardada
            password_hash = str.encode(account['password'])
            if bcrypt.checkpw(password, password_hash):
                session['loggedin'] = True
                session['id_user'] = account['id_user']
                session['email'] = account['email']
                return redirect(url_for('home'))
            else:
                msg = 'Incorrect password!'
        else:
            msg = 'Incorrect email!'
    return render_template('auth/login.html', msg=msg)

def logout():
   session.pop('loggedin', None)
   session.pop('id_user', None)
   session.pop('email', None)
   return redirect(url_for('login'))

def register():
    if session.get('loggedin') is not None:
        return redirect(url_for('home'))
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', name):
            msg = 'Username must contain only characters and numbers!'
        elif not name or not password or not email:
            msg = 'Please fill out the form!'
        else:
            password = str.encode(password)
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            password_hash = hashed.decode()
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)', (name, email, password_hash,))
            mysql.connection.commit()
            return redirect(url_for('login'))
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('auth/register.html', msg=msg)