#!/usr/bin/python
from flask import render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
import os
from app import app

from flask_mysqldb import MySQL
import MySQLdb.cursors
from app import mysql

#########################
# Métodos
#########################

#Método para cargar archivos.
def upload_files(id_analysis):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    return render_template('upload_file.html', id_analysis=id_analysis)

#Método para cargar archivos.
def save_files():
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    files = request.files.getlist("ourfiles")
    id_analysis = request.form['id_analysis']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    for file in files:
        if file and allowed_file(file.filename):
            file_name = file.filename
            filename = secure_filename(file.filename)
            if not file_already(filename, id_analysis):
                file.save("./app/static/uploads/files"+str(id_analysis)+"/"+filename)
                cursor.execute('INSERT INTO files VALUES (NULL, %s, %s, %s)', (id_analysis, file_name, filename,))
    mysql.connection.commit()
    return redirect(url_for('view_analysis', id_analysis=id_analysis))

#Método para ver un archivo.
def get_file(id_analysis, filename):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    if file_already(filename, id_analysis):
        return send_from_directory(app.config["UPLOAD_FOLDER"], "files"+str(id_analysis)+"/"+filename)
    #session["index_message"] = "Archivo no encontrado."
    return redirect(url_for('view_analysis', id_analysis=id_analysis))

#Método para eliminar un archivo.
def delete_file(id_analysis, filename):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    #session["index_message"] = "Error: Archivo no existe."
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM files WHERE id_analysis = %s AND file = %s', (id_analysis, filename,))
    mysql.connection.commit()
    #Remover archivo de directorio
    os.remove("./app/static/uploads/files"+str(id_analysis)+"/"+filename)
    return redirect(url_for('view_analysis', id_analysis=id_analysis))

#########################
# Métodos adicionales
#########################

#Validación de extensión de documento.
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"pdf"}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Validación si documento existe.
def file_already(filename, id_analysis):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM files WHERE id_analysis = %s AND file = %s', (id_analysis, filename))
    file = cursor.fetchone()
    if file:
        return True
    return False