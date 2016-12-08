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
from path import path
from bs4 import BeautifulSoup
from marcheolex.basededonnees import Version_texte
from marcheolex.basededonnees import Version_section
from marcheolex.basededonnees import Article
from marcheolex.utilitaires import normalisation_code
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import decompose_cid


def creer_markdown(textes, cache):
    
    for texte in textes:
        creer_markdown_texte(texte, cache)


def creer_markdown_texte(texte, cache):
    
    # Informations de base
    cid = texte[1]
    articles = Article.select(Article.id).where(Article.texte == cid)
    chemin_base = os.path.join(cache, 'bases-xml')
    if os.path.exists(os.path.join(chemin_base, chemin_texte(cid, True, True))):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, True, True))
    elif os.path.exists(os.path.join(chemin_base, chemin_texte(cid, True, False))):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, True, False))
    elif os.path.exists(os.path.join(chemin_base, chemin_texte(cid, False, True))):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, False, True))
    elif os.path.exists(os.path.join(chemin_base, chemin_texte(cid, False, False))):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, False, False))
    elif os.path.exists(os.path.join(chemin_base, chemin_texte(cid, True, True)+'.xml')):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, True, True))
    elif os.path.exists(os.path.join(chemin_base, chemin_texte(cid, True, False)+'.xml')):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, True, False))
    elif os.path.exists(os.path.join(chemin_base, chemin_texte(cid, False, True)+'.xml')):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, False, True))
    elif os.path.exists(os.path.join(chemin_base, chemin_texte(cid, False, False)+'.xml')):
        chemin_base = os.path.join(chemin_base, chemin_texte(cid, False, False))
    else:
        raise Exception()
    
    # Créer le répertoire de cache
    path(os.path.join(cache, 'markdown')).mkdir_p()
    path(os.path.join(cache, 'markdown', cid)).mkdir_p()
    
    for article in articles:
        
        # Si la markdownisation a déjà été faite, passer
        chemin_markdown = os.path.join(cache, 'markdown', cid, article.id + '.md')
        if os.path.exists(chemin_markdown):
            continue
        
        # Lecture du fichier
        chemin_article = os.path.join(chemin_base, 'article', decompose_cid(article.id) + '.xml')
        f_article = open(chemin_article, 'r')
        soup = BeautifulSoup(f_article.read(), 'xml')
        f_article.close()
        contenu = soup.find('BLOC_TEXTUEL').find('CONTENU').text.strip()
        
        # Logique de transformation en Markdown
        lignes = [l.strip() for l in contenu.split('\n')]
        contenu = '\n'.join(lignes)
        
        # - Retrait des <br/> en début et fin (cela semble être enlevé par BeautifulSoup)
        if all([lignes[l].startswith(('<br/>', r'<br />')) for l in range(0, len(lignes))]):
            lignes[i] = re.sub(r'^<br ?/> *', r'', lignes[i])
        if all([lignes[l].endswith(('<br/>', r'<br />')) for l in range(0, len(lignes))]):
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
        
        # Enregistrement
        f_markdown = open(chemin_markdown, 'w')
        f_markdown.write(contenu.encode('utf-8'))
        f_markdown.close()

