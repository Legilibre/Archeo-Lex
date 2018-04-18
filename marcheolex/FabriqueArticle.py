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
            if not article:
                self.articles[id] = ('INCONNU', '', None, None )
            id, section, num, date_debut, date_fin, bloc_textuel, cid = article

            date_debut = datetime.date(*(time.strptime(date_debut, '%Y-%m-%d')[0:3])) if date_debut != '2999-01-01' else None
            date_fin = datetime.date(*(time.strptime(date_fin, '%Y-%m-%d')[0:3])) if date_fin != '2999-01-01' else None

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

        # La période de vigueur de cet article est expiré ou expire : ne pas l’ajouter au texte (date_fin <= debut_vigueur_texte)
        # Le cas quasi-erroné où le texte n’a pas de début de vigueur est écarté ici, mais devrait probablement renvoyer une erreur ailleurs
        if debut_vigueur_texte and comp_infini_large( date_fin, debut_vigueur_texte ):
            return (None, date_debut, date_fin)

        # La période de vigueur de cet article n’est pas encore commencé (fin_vigueur_texte <= date_debut) 
        # Les articles intemporels (= sans date de début de vigueur (et normalement sans date de fin de vigueur)) sont considérés comme toujours en vigueur
        if date_debut and comp_infini_large( fin_vigueur_texte, date_debut ):
            return (None, date_debut, date_fin)

        if not self.cache:
            self.effacer_cache()

        # Enregistrement
        niveaux = [ False ] * niveau
        texte_retourne = FabriqueArticle.stockage.ecrire_ressource( id, niveaux, num.strip() if num else '', '', texte_article )

        return (num, texte_retourne, date_debut, date_fin)

# vim: set ts=4 sw=4 sts=4 et:
