#!/usr/bin/python
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from werkzeug.utils import secure_filename
from io import StringIO
import os, sys, getopt

UPLOAD_FOLDER = os.path.abspath("./uploads/")
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

#########################
# Rutas
#########################

#Metodo principal.
@app.route('/')
def index():
    archivos = []
    if session.get('num_files') is not None:
        for i in range(session["num_files"]+1):
            archivos.append(str(session["file"+str(i)]))
    conceptos = []
    if session.get('num_concept') is not None:
        for i in range(session["num_concept"]+1):
            conceptos.append(str(session["concept"+str(i)]))
    if session.get('index_message') is not None:
        message=session["index_message"]
        session.pop('index_message')
        return render_template('index.html' , archivos=archivos, conceptos=conceptos, message=message )
    return render_template('index.html' , archivos=archivos, conceptos=conceptos )

#Método para cargar archivos.
@app.route('/upload_files', methods=["GET", "POST"])
def upload_files():
    session["index_message"] = "success"
    if request.method == "POST":
        files = request.files.getlist("ourfiles")
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if not file_already(filename):
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    if session.get('num_files') is not None:
                        session["num_files"] = session["num_files"] + 1
                    else:
                        session["num_files"] = 0
                    session["file"+str(session["num_files"])] = filename
                else:
                    session["index_message"] = "Archivo ya existe."
            else:
                session["index_message"] = "No permitido."
        return redirect(url_for('.index'))
    return render_template('upload_file.html')

#Método para ver un archivo.
@app.route('/view/<filename>')
def get_file(filename):
    if file_already(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    session["index_message"] = "Archivo no encontrado."
    return redirect(url_for('.index'))

#Método para eliminar un archivo.
@app.route('/delete/<filename>')
def delete_file(filename):
    session["index_message"] = "Error: Archivo no existe."
    if session.get('num_files') is not None:
        for i in range(session["num_files"]+1):
            if filename == str(session["file"+str(i)]):
                os.remove("./uploads/"+session["file"+str(i)])
                renumber(i)
                session["index_message"] = "Success: Archivo eliminado."
                break
    return redirect(url_for('.index'))

#Método para agregar conceptos.
@app.route('/add_concept', methods=["POST"])
def add_concept():
    session["index_message"] = "Success: Concepto agregado"
    concept = request.form['concept']
    if not concept_already(concept):
        if session.get('num_concept') is not None:
            session["num_concept"] = session["num_concept"] + 1
        else:
            session["num_concept"] = 0
        session["concept"+str(session["num_concept"])] = concept
    else:
        session["index_message"] = "Concepto ya existe."
    return redirect(url_for('.index'))

#Método para editar un concepto.
@app.route('/edit_concept/<concept>',methods=["GET","POST"])
def edit_concept(concept):
    if request.method == "POST":
        concept = request.form['concept']
        id_concept = request.form['id_concept']
        session["concept"+id_concept] = concept
        session["index_message"] = "Succes: Concepto actualizado."
        return redirect(url_for('.index'))
    else:
        if session.get('num_concept') is not None:
            for i in range(session["num_concept"]+1):
                if concept == str(session["concept"+str(i)]):
                    return render_template('edit_concept.html', concept=concept, id_concept=i)
    session["index_message"] = "Error: Concepto no existe."
    return redirect(url_for('.index'))
    

#Método para eliminar un concepto.
@app.route('/delete_concept/<concept>')
def delete_concept(concept):
    session["index_message"] = "Error: Concepto no existe."
    if session.get('num_concept') is not None:
        for i in range(session["num_concept"]+1):
            if concept == str(session["concept"+str(i)]):
                renumber_concept(i)
                session["index_message"] = "Success: Concepto eliminado."
                break
    return redirect(url_for('.index'))

@app.route('/converttext')
def convert_to_text():
    pdfFilename = "uploads/Buhos_-_A_web-based_systematic_literature_review_management_software.pdf"
    text = convert(pdfFilename) #get string of text content of pdf
    text= text.replace("", "")
    text= text.replace("\n", " ")
    while text.find("  ") > 0:
        text= text.replace("  ", " ")
    print(text)
    return text

#########################
# Métodos
#########################

#Renumerar documentos en la sesión.
def renumber(position):
    for i in range(position ,session["num_files"]+1):
        if i < session["num_files"]:
            session["file"+str(i)] = session["file"+str(i+1)]
        else:
            session.pop("file"+str(i))
            session["num_files"] = session["num_files"] - 1

#Renumerar conceptos en la sesión.
def renumber_concept(position):
    for i in range(position ,session["num_concept"]+1):
        if i < session["num_concept"]:
            session["concept"+str(i)] = session["concept"+str(i+1)]
        else:
            session.pop("concept"+str(i))
            session["num_concept"] = session["num_concept"] - 1

#Validación de extensión de documento.
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Validación si documento existe.
def file_already(filename):
    if session.get('num_files') is not None:
        for i in range(session["num_files"]+1):
            if filename == str(session["file"+str(i)]):
                return True
    return False

#Validación si concepto existe.
def concept_already(concept):
    if session.get('num_concept') is not None:
        for i in range(session["num_concept"]+1):
            if concept == str(session["concept"+str(i)]):
                return True
    return False

#converts pdf, returns its text content as a string
def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    output = StringIO()
    manager = PDFResourceManager()
    infile = open(fname, 'rb')
    text = ""
    for page in PDFPage.get_pages(infile, pagenums):
        output = StringIO()
        converter = TextConverter(manager, output, laparams=LAParams())
        interpreter = PDFPageInterpreter(manager, converter)
        interpreter.process_page(page)
        #text = text + "<br><hr><br>\n" + output.getvalue()
        text = text + output.getvalue()
    infile.close()
    converter.close()
    output.close
    return text

if __name__ == '__main__':
# Para cambiar el puerto -> app.run( port=8000 ), debug = true para que se actualicen los cambios
    app.secret_key = "Python application"
    app.run( debug = True )