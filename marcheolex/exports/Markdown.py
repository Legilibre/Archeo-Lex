# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
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
import re
from . import Syntaxes


class Markdown( Syntaxes ):

    def transformer_depuis_html( self, html ):

        """
        Transformer un texte en Markdown à partir du HTML.

        :param html:
            (string) HTML à transformer.
        :returns:
            (string|None) Texte équivalent en Markdown.
        """

        # Transformation des <br/> en <p>
        texte = html
        if texte == None:
            texte = ''
        texte = re.sub(r'<br ?\/>', '\n', texte)
        texte = re.sub(r'<p>(.*?)<\/p>', r'\1\n\n', texte, flags=re.DOTALL)
        texte = re.sub(r'\n\n+', '\n\n', texte)

        # Retrait des espaces blancs de fin de ligne
        texte = '\n'.join([l.strip() for l in texte.split('\n')])
        texte = texte.strip()

        # - Markdownisation des listes numérotées
        #lignes = texte.split('\n')
        #ligne_liste = [ False ] * len(lignes)
        #for i in range(len(lignes)):
        #    if re.match(r'(?:\d+[°\.\)-]|[\*-]) ', lignes[i]):
        #        ligne_liste[i] = True
        #    lignes[i] = re.sub(r'^(\d+)([°\.\)-]) +', r'\1. ', lignes[i])
        #    lignes[i] = re.sub(r'^([\*-]) +', r'- ', lignes[i])

        # - Création d’alinea séparés, sauf pour les listes
        #texte = lignes[0]
        #for i in range(1, len(lignes)):
        #    if ligne_liste[i]:
        #        texte = texte + '\n' + lignes[i]
        #    else:
        #        texte = texte + '\n\n' + lignes[i]

        return texte

    def obtenir_titre( self, parents, texte ):

        """
        Obtenir le titre dans la syntaxe représentée.

        :param parents:
            (liste de strings) Niveaux parents de la ressource.  :param texte:
            (string) Texte du titre.
        :returns:
            (string|None) Texte du titre dans la syntaxe représentée.
        """

        marque_niveau = ''
        for i in range( len(parents) ):
            marque_niveau = marque_niveau + '#'

        return marque_niveau + ' ' + texte + '\n\n'


# vim: set ts=4 sw=4 sts=4 et:
