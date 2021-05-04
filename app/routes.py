#!/usr/bin/python
from app import app
from app import HomeController
from app import FilesController
from app import ConceptsController
from app import LoginController
import os

#########################
# Rutas 
#########################

#HomeController
app.add_url_rule('/', view_func=HomeController.index, methods=["GET"])
app.add_url_rule('/home', view_func=HomeController.home, methods=["GET"])
app.add_url_rule('/new_analysis', view_func=HomeController.new_analysis, methods=["POST"])
app.add_url_rule('/view_analysis/<id_analysis>', view_func=HomeController.view_analysis, methods=["GET"])
app.add_url_rule('/delete_analysis/<id_analysis>', view_func=HomeController.delete_analysis, methods=["GET"])
app.add_url_rule('/get_matriz/<id_analysis>', view_func=HomeController.get_text_pdf, methods=["GET"])
app.add_url_rule('/view_matriz/<id_analysis>', view_func=HomeController.view_matriz, methods=["GET"])
#app.add_url_rule('/compare', view_func=HomeController.compare, methods=["GET"])

#LoginController
app.add_url_rule('/login', view_func=LoginController.login, methods=["GET","POST"])
app.add_url_rule('/logout', view_func=LoginController.logout, methods=["GET"])
app.add_url_rule('/register', view_func=LoginController.register, methods=["GET","POST"])

#FilesController
app.add_url_rule('/save_files', view_func=FilesController.save_files, methods=["POST"])
app.add_url_rule('/view_file/<id_analysis>/<filename>', view_func=FilesController.get_file, methods=["GET"])
app.add_url_rule('/delete_file/<id_analysis>/<filename>', view_func=FilesController.delete_file, methods=["GET"])

#ConceptsController
app.add_url_rule('/add_concept', view_func=ConceptsController.add_concept, methods=["POST"])
app.add_url_rule('/update_concept', view_func=ConceptsController.update_concept, methods=["POST"])
app.add_url_rule('/delete_concept/<id_analysis>/<concept>', view_func=ConceptsController.delete_concept, methods=["GET"])