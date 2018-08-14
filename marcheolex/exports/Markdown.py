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

        texte = html
        if texte == None:
            return ''

        # Syntaxes inutiles
        texte = re.sub(r'</b><b>', '', texte)

        # Transformation des <br>, <p>, <div>, <span>, <blockquote> en paragraphes Markdown
        # - Les deux blockquote successifs servent lorsque deux blockquote sont imbriqués (souvent)
        texte = re.sub(r'<br((?: [^>]*)?)/?>', '\n\n', texte)
        texte = re.sub(r'<p align="center"(?:(?: [^>]*)?)>(.*?)</p>', r'<center>\1</center>', texte, flags=re.DOTALL)
        texte = re.sub(r'<p(?:(?: [^>]*)?)>(.*?)</p>', r'\1\n\n', texte, flags=re.DOTALL)
        texte = re.sub(r'<div(?:(?: [^>]*)?)>(.*?)</div>', r'\1\n\n', texte, flags=re.DOTALL)
        texte = re.sub(r'<span(?:(?: [^>]*)?)>(.*?)</span>', r'\1\n\n', texte, flags=re.DOTALL)
        texte = re.sub(r'<blockquote>(.*?)</blockquote>', r'\n\n\1\n\n', texte, flags=re.DOTALL)
        texte = re.sub(r'<blockquote>(.*?)</blockquote>', r'\n\n\1\n\n', texte, flags=re.DOTALL)

        # Les balises de tableau vont sur des lignes séparées
        texte = re.sub(r'\s*<td(?: align="left"| width="\d+")*((?: [^>]*)?)>\s*(.*?)\s*</td>\s*', r'\n<td\1>\2</td>\n', texte, flags=re.DOTALL)
        texte = re.sub(r'\s*<th(?: align="left"| width="\d+")*((?: [^>]*)?)>\s*(.*?)\s*</th>\s*', r'\n<th\1>\2</th>\n', texte, flags=re.DOTALL)
        texte = re.sub(r'\s*<tr(?: align="left"| width="\d+")*((?: [^>]*)?)>\s*', r'\n<tr\1>\n', texte, flags=re.DOTALL)
        texte = re.sub(r'\s*</tr>\s*', '\n</tr>\n', texte, flags=re.DOTALL)
        texte = re.sub(r'\s*<table((?: [^>]*)?)>', r'\n\n<table\1>', texte, flags=re.DOTALL)
        texte = re.sub(r'\s*</table>', '</table>\n\n', texte, flags=re.DOTALL)

        # Retrait des espaces blancs en début et fin de ligne
        texte = re.sub(r'(?:[ \t\r\f\v]+|</[a-z]+>)*$', lambda m: m.group(0).replace(' ', ''), texte, flags=re.MULTILINE)
        texte = re.sub(r'^((?:<[a-z]+(?: [^>]*)?>)*)[ \t\r\f\v]+', r'\1', texte, flags=re.MULTILINE)
        texte = re.sub(r'^((?:<[a-z]+(?: [^>]*)?>)*)[ \t\r\f\v]+', r'\1', texte, flags=re.MULTILINE)
        texte = re.sub(r'^((?:<[a-z]+(?: [^>]*)?>)*)[ \t\r\f\v]+', r'\1', texte, flags=re.MULTILINE)

        # Markdownisation des listes à puces
        # - Les sept tirets sont U+002D, U+2010 et U+2011, U+2012 et U+2013, U+2014 et U+2015
        # - La 2e expression sert à ajouter une ligne vide avant une liste à puces
        texte = re.sub(r'\n+[-‐‑‒–—―] *([^\n]+)', r'\n- \1', texte)
        texte = re.sub(r'\n([^-][^\n]*)\n-([^\n]+)', r'\n\1\n\n-\2', texte)

        # Markdownisation des listes numérotées
        # - Certains convertisseurs Markdown → HTML renumérotent à partir de 1 dès que ça ressemble à une
        #   liste numérotée, ce qui bien sûr fait perdre ladite numérotation ; pour éviter cela, les listes
        #   numérotées ne sont pas transformées en syntaxe Markdown. Un point également à prendre en compte
        #   est que le signe par défaut est ° (par ex. 1°), ce qui serait probablement perdu en Markdown,
        #   faisant s’éloigner du texte original.
        #lignes = texte.split('\n')
        #ligne_liste = [ False ] * len(lignes)
        #for i in range(len(lignes)):
        #    if re.match(r'(?:\d+[°\.\)-]|[\*-]) ', lignes[i]):
        #        ligne_liste[i] = True
        #    lignes[i] = re.sub(r'^(\d+)([°\.\)-]) +', r'\1. ', lignes[i])
        #    lignes[i] = re.sub(r'^([\*-]) +', r'- ', lignes[i])

        # Lorsque trop d’espaces consécutifs sont présents, limiter à un maximum de 1
        texte = re.sub(r' {2,}', ' ', texte)

        # Ajouter des espaces blancs en début de ligne des tableaux
        texte = re.sub(r'\n*<td((?: [^>]*)?)>(.*?)</td>', r'\n  <td\1>\2</td>', texte, flags=re.DOTALL)
        texte = re.sub(r'\n*<th((?: [^>]*)?)>(.*?)</th>', r'\n  <th\1>\2</th>', texte, flags=re.DOTALL)
        texte = re.sub(r'\n*<tr((?: [^>]*)?)>\n*', r'\n <tr\1>\n', texte, flags=re.DOTALL)
        texte = re.sub(r'\n*</tr>\n*', '\n </tr>\n', texte, flags=re.DOTALL)

        # Lorsque trop de retours à la ligne consécutifs sont présents, limiter à un maximum de 2
        texte = re.sub(r'\n{3,}', '\n\n', texte)

        texte = texte.strip()

        return texte


    def ajouter_liens( self, texte, liens_internes, liens_externes ):

        """
        Ajouter des liens dans un texte.

        :param texte:
            (string) Texte où ajouter les liens.
        :param liens_internes:
            (dictionnaire string: string) Liste des liens internes à ajouter dans le texte.
        :param liens_externes:
            (dictionnaire string: string) Liste des liens externes à ajouter dans le texte.
        :returns:
            (string) Texte avec liens.
        """

        for lien in liens_internes:

            texte = re.sub( lien, '[' + lien + '](#' + liens_internes[lien] + ')', texte )

        for lien in liens_externes:

            texte = re.sub( lien, '[' + lien + '](' + liens_externes[lien] + ')', texte )

        return texte


    def obtenir_titre( self, parents, texte ):

        """
        Obtenir le titre dans la syntaxe représentée.

        :param parents:
            (liste de strings) Niveaux parents de la ressource.
        :param texte:
            (string) Texte du titre.
        :returns:
            (string|None) Texte du titre dans la syntaxe représentée.
        """

        marque_niveau = '#' * len(parents)

        texte = re.sub( r'(&#13;)?\n*', '', texte ).strip()

        return marque_niveau + ' ' + texte + '\n\n'

# vim: set ts=4 sw=4 sts=4 et:
