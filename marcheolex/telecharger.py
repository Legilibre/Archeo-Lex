# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module télécharge diverses donnés et métadonnées depuis Légifrance
# 
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# the LICENSE file for more details.

# Imports
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import re
from datetime import datetime
from path import path
from bs4 import BeautifulSoup
from marcheolex.utilitaires import telecharger
from marcheolex.utilitaires import MOIS
from marcheolex.utilitaires import nop


def telecharger_legifrance(url, fichier, cache_html, force=False):

    if os.path.exists(os.path.join(cache_html, fichier)):
        touch = datetime.fromtimestamp(os.stat(os.path.join(cache_html, fichier)).st_mtime)
        delta = datetime.today() - touch
        
        if not force or not isinstance(force, bool) and isinstance(force, (int, long, float)) and delta.total_seconds() < force:
            print('* Téléchargement de ' + url + ' (cache)')
            return True
    
    print('* Téléchargement de ' + url)
    return telecharger('http://legifrance.gouv.fr/' + url, os.path.join(cache_html, fichier))


def telecharger_html(cles, cache):
    
    path(os.path.join(cache, 'html')).mkdir_p()
    path(os.path.join(cache, 'xml-html')).mkdir_p()
    
    # Télécharger effectivement les fichiers HTML (ou vérifier qu’ils sont dans le cache)
    telecharger_html_reel(cles, os.path.join(cache, 'html'))
    
    # Transformer le HTML en XML
    transformer_html_xml(cles, cache)


def telecharger_html_reel(cles, cache):
     
    for cle in cles:
        
        nom_index = 'affichTexte.do'
        if cle[2]:
            nom_index = 'affichCode.do'
        
        # Téléchargement initial
        telecharger_legifrance(nom_index + '?cidTexte=' + cle[1], cle[1] + '.html', cache, 86400)
        fichier = open(os.path.join(cache, cle[1] + '.html'), 'r')
        
        # Recherche de la version consolidée la plus récente
        soup = BeautifulSoup(fichier.read())
        date = soup.select('.sousTitreTexte')
        if date and re.match(('Version consolidée au \d{1,2} (?:' + '|'.join(MOIS.keys()) + ') \d{4}'), date[0].text.strip()):
            date = re.match(('Version consolidée au (\d{1,2}) (' + '|'.join(MOIS.keys()) + ') (\d{4})'), date[0].text.strip())
            date = date.group(3) + MOIS[date.group(2)] + '{:02d}'.format(int(date.group(1)))
            telecharger_legifrance(nom_index + '?cidTexte=' + cle[1] + '&dateTexte=' + date, cle[1] + '-' + date + '.html', cache)


def transformer_html_xml(cles, cache):
    nop()


# Le tuple renvoyé correspond à (Nom, cidTexte, estUnCode, 'xml'|'xml-html'|'html'|None)
def obtenir_identifiants(cles, cache):
    
    codes, sedoc = telecharger_index_codes(cache)
    
    ncles = [''] * len(cles)
    for i in range(0, len(cles)):
        
        cle = re.sub('’', '\'', re.sub('[_-]', ' ', cles[i]))
        cle = cle[0].upper() + cle[1:].lower()
        
        if cle == 'Constitution de 1958' or cle.upper() == 'LEGITEXT000006071194':
            ncles[i] = ('Constitution de 1958', 'LEGITEXT000006071194', False, None)
        elif cle in sedoc.keys():
            ncles[i] = (re.sub('\'', '’', cle), sedoc[cle], True, None)
        elif cle.upper() in codes.keys():
            ncles[i] = (codes[cle.upper()], cle.upper(), True, None)
        else:
            ncles[i] = (None, cles[i], None, None)
    
    return ncles


def telecharger_index_codes(cache):
    
    codes = {}
    sedoc = {}
    
    # Télécharger le cas échéant le formulaire de recherche contenant le nom des codes
    path(os.path.join(cache, 'html')).mkdir_p()
    telecharger_legifrance('initRechCodeArticle.do', 'recherche.html', os.path.join(cache, 'html'), 86400)
    fichier_recherche = open(os.path.join(cache, 'html', 'recherche.html'), 'r')
    soup = BeautifulSoup(fichier_recherche.read())
    
    # Récupérer les informations
    codes_html = soup.select('select[name="cidTexte"]')[0].findAll('option')
    for code_html in codes_html:
        if code_html.has_attr('title') and code_html.has_attr('value'):
            codes[code_html.attrs['value']] = code_html.attrs['title']
            sedoc[code_html.attrs['title']] = code_html.attrs['value']
    
    return codes, sedoc

