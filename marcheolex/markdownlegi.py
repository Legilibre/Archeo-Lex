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
from path import Path


def creer_markdown(textes, db, cache):

    for texte in textes:
        creer_markdown_texte(texte, db, cache)


def creer_markdown_texte(textecid, db, cache):

    # Informations de base
    cid = textecid[1]
    articles = db.all("""
        SELECT id, bloc_textuel
        FROM articles
        WHERE cid = '{0}'
    """.format(cid))

    # Créer le répertoire de cache
    Path(os.path.join(cache, 'markdown')).mkdir_p()
    Path(os.path.join(cache, 'markdown', cid)).mkdir_p()

    for article in articles:

        # Si la markdownisation a déjà été faite, passer
        chemin_markdown = os.path.join(cache, 'markdown', cid, article[0] + '.md')
        if os.path.exists(chemin_markdown):
            continue

        # Transformation des <br/> en <p>
        texte = article[1]
        if texte == None:
            texte = ''
        texte = re.sub(r'<br ?\/>', '\n', texte)
        texte = re.sub(r'<p>(.*?)<\/p>', r'\1\n\n', texte, flags=re.DOTALL)
        texte = re.sub(r'\n\n+', '\n\n', texte)

        # Retrait des espaces blancs de fin de ligne
        texte = '\n'.join([l.strip() for l in texte.split('\n')])
        texte = texte.strip()

        # - Markdownisation des listes numérotées
        lignes = texte.split('\n')
        ligne_liste = [ False ] * len(lignes)
        for i in range(len(lignes)):
            if re.match(r'(?:\d+[°\.\)-]|[\*-]) ', lignes[i]):
                ligne_liste[i] = True
            lignes[i] = re.sub(r'^(\d+)([°\.\)-]) +', r'\1. ', lignes[i])
            lignes[i] = re.sub(r'^([\*-]) +', r'- ', lignes[i])

        # - Création d’alinea séparés, sauf pour les listes
        #texte = lignes[0]
        #for i in range(1, len(lignes)):
        #    if ligne_liste[i]:
        #        texte = texte + '\n' + lignes[i]
        #    else:
        #        texte = texte + '\n\n' + lignes[i]

        # Enregistrement
        f_markdown = open(chemin_markdown, 'w')
        f_markdown.write(texte.encode('utf-8'))
        f_markdown.close()

# vim: set ts=4 sw=4 sts=4 et:
