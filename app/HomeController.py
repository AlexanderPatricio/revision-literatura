#!/usr/bin/python
from flask import render_template, session, redirect, url_for, request
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from app import app
import os
import re
#Librerias para la comparación del texto
import gensim.downloader as api
from gensim.models  import Word2Vec
from gensim import models
import numpy as np
from collections import Counter
import itertools
from sklearn.metrics.pairwise import cosine_similarity
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from unidecode import unidecode
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer

from flask_mysqldb import MySQL
import MySQLdb.cursors
from app import mysql

#########################
# Métodos
#########################

def index():
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

#Metodo principal.
def home():
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM analysis WHERE id_user = %s AND status != "2"', (session.get('id_user'),))
    analysis = cursor.fetchall()
    return render_template('home.html', analysis=analysis)

def new_analysis():
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    name = request.form['name']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('INSERT INTO analysis VALUES (NULL, %s, %s, %s)', (session.get('id_user'), name, 0))
    mysql.connection.commit()
    cursor.execute('SELECT * FROM analysis WHERE id_user = %s ORDER BY id_analysis DESC LIMIT 1', (session.get('id_user'),))
    analysis = cursor.fetchone()
    os.mkdir("./app/static/uploads/files"+str(analysis['id_analysis']))
    return redirect(url_for('view_analysis', id_analysis=analysis['id_analysis']))

def view_analysis(id_analysis):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM analysis WHERE id_analysis = %s AND status != "2"', (id_analysis,))
    analysis = cursor.fetchone()
    if id_analysis.isdigit() and analysis:
        #Get database files
        cursor.execute('SELECT * FROM files WHERE id_analysis = %s', (id_analysis,))
        files = cursor.fetchall()
        #Get database concepts
        cursor.execute('SELECT * FROM concepts WHERE id_analysis = %s', (id_analysis,))
        concepts = cursor.fetchall()
        return render_template('view_analysis.html' , files=files, concepts=concepts, id_analysis=id_analysis, name_analysis=analysis['name'], status=analysis['status'] )
    return redirect(url_for('home'))

def delete_analysis(id_analysis):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM analysis WHERE id_analysis = %s', (id_analysis,))
    analysis = cursor.fetchone()
    if id_analysis.isdigit() and analysis:
        cursor.execute('UPDATE analysis SET status = 2 WHERE id_analysis = %s', (id_analysis,))
        mysql.connection.commit()
    return redirect(url_for('home'))

def view_matriz(id_analysis):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM analysis WHERE id_analysis = %s', (id_analysis,))
    analysis = cursor.fetchone()
    if id_analysis.isdigit() and analysis and analysis['status'] == "1":
        #Get database files
        cursor.execute('SELECT * FROM files WHERE id_analysis = %s', (id_analysis,))
        files = cursor.fetchall()
        #Get database concepts
        cursor.execute('SELECT * FROM concepts WHERE id_analysis = %s', (id_analysis,))
        concepts = cursor.fetchall()
        results = []
        sentences = []
        for file in files:
            for concept in concepts:
                cursor.execute('SELECT * FROM results WHERE id_file = %s AND id_concept = %s', (file['id_file'],concept['id_concept']))
                result = cursor.fetchone()
                results.append(result)
                cursor.execute('SELECT * FROM sentences WHERE id_result = %s', (result['id_result'],))
                sentence = cursor.fetchall()
                sentences.append(sentence)
        return render_template('view_matriz.html' , files=files, concepts=concepts, results=results, sentences=sentences, id_analysis=id_analysis ,name_analysis=analysis['name'] )
    return redirect(url_for('home'))

#Metodo para extraer texto PDF
def get_text_pdf(id_analysis):
    if session.get('loggedin') is None:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM analysis WHERE id_analysis = %s', (id_analysis,))
    analysis = cursor.fetchone()
    if id_analysis.isdigit() and analysis and analysis['status'] == "0":
        #Get database files
        cursor.execute('SELECT * FROM files WHERE id_analysis = %s', (id_analysis,))
        files = cursor.fetchall()
        #Get database concepts
        cursor.execute('SELECT * FROM concepts WHERE id_analysis = %s', (id_analysis,))
        concepts = cursor.fetchall()
        r = []
        r_sentences = []
        ###rp = ""
        if(len(files) == 0 or len(concepts) == 0):
            return redirect(url_for('view_analysis', id_analysis=id_analysis))
        for file in files:
            #print(file['file'])
            pdfFilename = app.config["UPLOAD_FOLDER"]+"/files"+str(id_analysis)+"/"+file['file']
            text = convert(pdfFilename) #get string of text content of pdf
            text = text.replace(""," ")            
            #References
            text = text.replace("\nREFERENCES\n","\nReferences\n")
            textsplit = text.split("\nReferences\n")
            #print(len(textsplit))
            #if len(textsplit) > 2:
            if len(textsplit) >= 2:
                text = textsplit[0]
                for i in range(1,(len(textsplit)-1)):
                    text = text + textsplit[i]
            elif len(textsplit) == 1:
                text = text.replace("REFERENCES","References")
                aux = text.split("References")
                if len(aux) == 2:
                    text = aux[0]
            text = text.replace("\n", " ")
            #2352-7110/© 2018 the-authors.
            text = re.sub("([0-9]+\-[0-9]+\/© [0-9][0-9][0-9][0-9] [A-Za-z]+ [A-Za-z]+\.)", "", text)
            #© 2018 the-authors.
            text = re.sub("(© [0-9][0-9][0-9][0-9] [A-Za-z]+ [A-Za-z]+\.)", "", text)
            #Emails
            text = re.sub("([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})", "", text)
            #Urls
            text = re.sub("((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*", " ", text)
            text = text.replace("et al.", " ")
            text = text.replace("fig.", " ")
            text = text.replace("Fig.", " ")
            #(M.G. Morales Malverde)
            text = re.sub("\(([A-Z][a-záéíóúñ]*(\.|)(| ))+\)", "", text)
            #Morales Malverde
            text = re.sub("[A-Z][a-záéíóúñ]* [A-Z][a-záéíóúñ]*([A-Z][a-záéíóúñ]| )*", "", text)
            #(sec1.2.2)
            text = re.sub("\(([0-9a-z]*(\.|))+\)", "", text)
            #[15–17] 
            text = re.sub("\[([0-9]|-|–|,|\(|\)|[a-z]*| )+\]", "", text)
            #text = re.sub("\[([A-Za-z0-9]| )+\]", "", text)
            while text.find("  ") > 0:
                text= text.replace("  ", " ")
            #. 2.2.
            #text = re.sub("\. 2\.2\.", "Alexanderrrrr ", text) 
            text = re.sub("\. [1-9]+\.([0-9]+(\.|))*", ". ", text)
            #text = re.sub("[A-Za-z]\.", ". ", text)
            #return text
            sentences = sent_tokenize(text)
            my_list = []
            list_sentences = []
            
            for con in concepts:
                suma = 0
                cont = 0
                cont2 = 0
                max_sentences = [0, 0, 0]
                vec_sentences = ["", "", ""]
                concept = con['concept']
                for sentence in sentences:
                    #Limpieza de datos
                    sentence1 = pre_process(concept)
                    sentence2 = pre_process(sentence)
                    #Vector de oraciones con las palabras existentes en word_emb_model
                    sentence1 = [token for token in sentence1.split() if token in word_emb_model.wv.vocab]
                    sentence2 = [token for token in sentence2.split() if token in word_emb_model.wv.vocab]
                    if len(sentence1) > 0 and len(sentence2) > 0:
                        comparacion = compare(sentence1,sentence2)
                        if comparacion > 0.4:
                            cont2 = cont2 + 1
                            if comparacion > max_sentences[0]:
                                max_sentences[2] = max_sentences[1]
                                vec_sentences[2] = vec_sentences[1]
                                max_sentences[1] = max_sentences[0]
                                vec_sentences[1] = vec_sentences[0]
                                max_sentences[0] = comparacion
                                vec_sentences[0] = sentence
                            elif comparacion > max_sentences[1]:
                                max_sentences[2] = max_sentences[1]
                                vec_sentences[2] = vec_sentences[1]
                                max_sentences[1] = comparacion
                                vec_sentences[1] = sentence
                            elif comparacion > max_sentences[2]:
                                max_sentences[2] = comparacion
                                vec_sentences[2] = sentence
                        cont = cont + 1
                        suma = suma + comparacion
                        ###rp=rp+"Concepto: "+str(con['concept'])+"<br>Oración: "+sentence+"<br>Resultado: "+str(comparacion)+"<hr>"
                answer = "0.0%"
                if cont > 0:
                    answer = str(round(((cont2*100)/cont), 2))+"%"
                cursor.execute('INSERT INTO results VALUES (NULL, %s, %s, %s)', (file['id_file'], con['id_concept'],answer))
                if answer != "0.0%":
                    cursor.execute('SELECT * FROM results WHERE id_file = %s and id_concept = %s ORDER BY id_result DESC LIMIT 1', (file['id_file'], con['id_concept'],))
                    last_result = cursor.fetchone()
                    for sentence in vec_sentences:
                        cursor.execute('INSERT INTO sentences VALUES (NULL, %s, %s)', (last_result['id_result'], sentence))
                
                my_list.append(answer)
                list_sentences.append(vec_sentences)
            r.append(my_list)
            r_sentences.append(list_sentences)
        ###return rp
        cursor.execute('UPDATE analysis SET status = 1 WHERE id_analysis = %s', (id_analysis,))
        mysql.connection.commit()
        return redirect(url_for('view_matriz', id_analysis=id_analysis))
    return redirect(url_for('home'))

word_emb_model = models.KeyedVectors.load_word2vec_format('Model-vectors-300.bin', binary=True)
#word_emb_model = models.KeyedVectors.load_word2vec_format('PubMed-w2v.bin', binary=True)
#word_emb_model = Word2Vec.load('word2vec_text8.model')
#Metodo para comparar documentos con conceptos
def compare(sentence1,sentence2):
    word_counts = Counter(itertools.chain(*(sentence1 + sentence2)))
    embedding_size = 300 #Model-vectors 300; PovMed 200; Word2vec.model 100; size of vectore in word embeddings
    a = 0.001
    sentence_set=[]
    for sentence in [sentence1, sentence2]:
        vs = np.zeros(embedding_size)
        sentence_length = len(sentence)
        for word in sentence:
            a_value = a / (a + word_counts[word]) # smooth inverse frequency, SIF
            aux = np.multiply(a_value, word_emb_model.wv[word])
            vs = np.add(vs, aux) # vs += sif * word_vector
        vs = np.divide(vs, sentence_length) # weighted average
        sentence_set.append(vs)
    res = cosine_similarity(sentence_set[0].reshape(1, -1), sentence_set[1].reshape(1, -1))[0][0]
    return res

lemmatizer = WordNetLemmatizer()
#Limpieza de oraciones
def pre_process(corpus):
    corpus = corpus.lower()
    stopset = stopwords.words('english') + list(string.punctuation)
    corpus = " ".join([i for i in word_tokenize(corpus) if i not in stopset])
    corpus = unidecode(corpus)
    words = word_tokenize(corpus)
    words_stem=[]
    for w in words:
        words_stem.append(lemmatizer.lemmatize(w))   
    corpus = " ".join(words_stem)
    return corpus


#########################
# Métodos adicionales
#########################

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