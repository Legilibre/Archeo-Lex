# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module transforme les articles en syntaxe Markdown
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
import hashlib

from path import path
from bs4 import BeautifulSoup

from marcheolex import condensat_tronque
from marcheolex import version_markdown
from marcheolex.basededonnees import Version_texte
from marcheolex.basededonnees import Version_section
from marcheolex.basededonnees import Version_article
from marcheolex.basededonnees import Travaux_articles
from marcheolex.utilitaires import normalisation_code
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import decompose_cid
from marcheolex.ranger import compteur_recursif


def creer_markdown(textes, cache):
    
    for texte in textes:
        creer_markdown_texte(texte, cache)


def creer_markdown_texte(texte, cache):
    
    # Informations de base
    cid = texte[1]
    articles = Travaux_articles.select(Travaux_articles, \
        Version_article).join(Version_article) \
        .where(Version_article.texte == cid).execute()
    
    # Créer le répertoire de cache
    path(os.path.join(cache, 'markdown')).mkdir_p()
    path(os.path.join(cache, 'markdown', cid)).mkdir_p()
    
    compteur_recursif(0)
    
    for i, article in enumerate(articles):
        
        compteur_recursif(i+1)
        
        # Si la markdownisation a déjà été faite, passer
        id = article.version_article.id
        chemin_xml = article.chemin
        condensat = str(article.version_article.condensat)
        chemin_markdown = os.path.join(cache, 'markdown', cid, \
                                       id + '-' + condensat + '.md')
        if condensat and os.path.exists(chemin_markdown):
            continue
        
        # Lecture du fichier
        f_article = open(chemin_xml, 'r')
        soup = BeautifulSoup(f_article.read(), 'xml')
        f_article.close()
        contenu = soup.find('BLOC_TEXTUEL').find('CONTENU').text.strip()
        
        # Logique de transformation en Markdown
        lignes = [l.strip() for l in contenu.split('\n')]
        contenu = '\n'.join(lignes)
        
        # - Retrait des <br/> en début et fin
        # (cela semble être enlevé par BeautifulSoup)
        if all([lignes[l].startswith(('<br/>', r'<br />'))
                                              for l in range(0, len(lignes))]):
            lignes[i] = re.sub(r'^<br ?/> *', r'', lignes[i])
        if all([lignes[l].endswith(('<br/>', r'<br />'))
                                              for l in range(0, len(lignes))]):
            lignes[i] = re.sub(r' *<br ?/>$', r'', lignes[i])
        contenu = '\n'.join(lignes)
        
        # - Markdownisation des listes numérotées
        ligne_liste = [ False ] * len(lignes)
        for i in range(len(lignes)):
            if re.match(r'(?:\d+[°\.\)-]|[\*-]) ', lignes[i]):
                ligne_liste[i] = True
            lignes[i] = re.sub(r'^(\d+)([°\.\)-]) +', r'\1. ', lignes[i])
            lignes[i] = re.sub(r'^([\*-]) +', r'- ', lignes[i])
        contenu = '\n'.join(lignes)
        
        # - Création d’alinea séparés, sauf pour les listes
        contenu = lignes[0]
        for i in range(1, len(lignes)):
            if ligne_liste[i]:
                contenu = contenu + '\n' + lignes[i]
            else:
                contenu = contenu + '\n\n' + lignes[i]
        
        # Calcul du condensat
        md5 = hashlib.md5(contenu.encode('utf-8')).hexdigest()
        condensat = md5[0:condensat_tronque]
        ambiguite = 0
        chemin_markdown = os.path.join(cache, 'markdown', cid,
            id + '-' + condensat + str(ambiguite) + '.md')
        while os.path.exists(chemin_markdown):
            f_markdown = open(chemin_markdown, 'w')
            texte_markdown = f_markdown.read()
            f_markdown.close()
            if md5 == hashlib.md5(texte_markdown).hexdigest():
                break
            ambiguite = ambiguite+1
            chemin_markdown = os.path.join(cache, 'markdown', cid,
                id + '-' + condensat + str(ambiguite) + '.md')
            if ambiguite == 10:
                raise Exception()
        
        # Enregistrement du fichier
        f_markdown = open(chemin_markdown, 'w')
        f_markdown.write(contenu.encode('utf-8'))
        f_markdown.close()
        
        # Inscription dans la base de données
        Version_article.update(condensat = condensat+str(ambiguite)) \
                       .where(Version_article.id == id).execute()
        
        Travaux_articles.delete() \
                        .where(Travaux_articles.id == article.id).execute()
        
        compteur_recursif()

