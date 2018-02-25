# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module assemble les textes et fait l’export final
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
import subprocess
import datetime
import time
import re
from pytz import timezone
from string import strip, join
from path import Path
from bs4 import BeautifulSoup
import legi
import legi.utils
from marcheolex import logger
from marcheolex import version_archeolex
from marcheolex import natures
from marcheolex.markdownlegi import creer_markdown
from marcheolex.markdownlegi import creer_markdown_texte
from marcheolex.utilitaires import normalisation_code
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import nop
from marcheolex.utilitaires import MOIS
from marcheolex.utilitaires import MOIS2
from marcheolex.utilitaires import comp_infini
from marcheolex.utilitaires import comp_infini_strict
from marcheolex.utilitaires import comp_infini_large
from marcheolex.exports.Syntaxes import Syntaxes
from marcheolex.exports.Markdown import Markdown

class FabriqueArticle:

    def __init__( self, db, stockage, cache = None, depr_cache = '' ):

        """
        :param db:
            Base de donnée.
        :param cache:
            boolean Utilisation d’un cache mémoire
        """

        FabriqueArticle.db = db
        FabriqueArticle.stockage = stockage

        self.cache = cache
        self.depr_cache = depr_cache
        self.articles = {}


    def effacer_cache():

        self.articles = {}


    def obtenir_texte_article( self, niveau, id, debut_vigueur_texte, fin_vigueur_texte, etat_vigueur_section ):

        """
        Obtenir le texte d’un article donné par un id.

        :param id:
            string - ID de l’article.
        :param debut_vigueur_texte:
            datetime.date - date de début de vigueur demandée.
        :param fin_vigueur_texte:
            datetime.date - date de fin de vigueur autorisée par la requête.
        :param etat_vigueur_section:
            string - état de la section
        :returns:
            (string, string, datetime.date, datetime.date) - (num, texte, debut_vigueur, fin_vigueur) Numéro et texte de l’article, dates de début et fin de vigueur.
        """

        if id not in self.articles:

            article = FabriqueArticle.db.one("""
                SELECT id, section, num, date_debut, date_fin, bloc_textuel, cid
                FROM articles
                WHERE id = '{0}'
            """.format(id))
            id, section, num, date_debut, date_fin, bloc_textuel, cid = article
            date_debut = datetime.date(*(time.strptime(date_debut, '%Y-%m-%d')[0:3]))
            if date_fin == '2999-01-01':
                date_fin = None
            else:
                date_fin = datetime.date(*(time.strptime(date_fin, '%Y-%m-%d')[0:3]))

            chemin_markdown = os.path.join(self.depr_cache, 'markdown', cid, id + '.md')
            if self.depr_cache and os.path.exists( chemin_markdown ):
                f_article = open(chemin_markdown, 'r')
                texte_article = f_article.read().decode('utf-8')
                f_article.close()
            else:
                md = Markdown()
                texte_article = md.transformer_depuis_html( bloc_textuel )

            self.articles[id] = (num, texte_article, date_debut, date_fin)

        num, texte_article, date_debut, date_fin = self.articles[id]

        # date_debut ≤ date_debut_vigueur
        if comp_infini_large(date_debut, debut_vigueur_texte):
            return (None, date_debut, date_fin)

        # date_fin_vigueur ≤ date_fin and retat != 'VIGUEUR'
        if comp_infini_large(fin_vigueur_texte, date_fin) and etat_vigueur_section != 'VIGUEUR':
            return (None, date_debut, date_fin)

        if not self.cache:
            self.effacer_cache()

        # Enregistrement
        niveaux = [ False ] * niveau
        texte_retourne = self.stockage.ecrire_ressource( id, niveaux, num.strip() if num else '', '', texte_article )

        return (num, texte_retourne, date_debut, date_fin)

# vim: set ts=4 sw=4 sts=4 et:
