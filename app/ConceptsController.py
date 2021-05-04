#!/usr/bin/python
from flask import render_template, request, redirect, url_for, session
#from app import app
from flask_mysqldb import MySQL
import MySQLdb.cursors
from app import mysql

#########################
# Métodos
#########################

#Método para agregar conceptos.
def add_concept():
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    #session["index_message"] = "Success: Concepto agregado"
    concept = request.form['concept']
    id_analysis = request.form['id_analysis']
    if not concept_already(concept, id_analysis):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO concepts VALUES (NULL, %s, %s)', (id_analysis, concept,))
        mysql.connection.commit()
    return redirect(url_for('view_analysis', id_analysis=id_analysis))

#Método para editar un concepto.
def edit_concept(id_analysis, concept):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM concepts WHERE id_analysis = %s AND concept = %s', (id_analysis, concept))
    concept = cursor.fetchone()
    if concept:
        return render_template('view_concept.html', concept=concept, id_analysis=id_analysis)
    #session["index_message"] = "Error: Concepto no existe."
    return redirect(url_for('view_analysis', id_analysis=id_analysis))


#Método para editar un concepto.
def update_concept():
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    concept = request.form['concept']
    id_concept = request.form['id_concept']
    id_analysis = request.form['id_analysis']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE concepts SET concept = %s WHERE id_concept = %s', (concept, id_concept))
    mysql.connection.commit()
    return redirect(url_for('view_analysis', id_analysis=id_analysis))


#Método para eliminar un concepto.
def delete_concept(id_analysis, concept):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM concepts WHERE id_analysis = %s AND concept = %s', (id_analysis, concept,))
    mysql.connection.commit()
    return redirect(url_for('view_analysis', id_analysis=id_analysis))

#########################
# Métodos adicionales
#########################

#Validación si concepto existe.
def concept_already(concept, id_analysis):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM concepts WHERE id_analysis = %s AND concept = %s', (id_analysis, concept))
    concept = cursor.fetchone()
    if concept:
        return True
    return False