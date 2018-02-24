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

class FabriqueSection:

    fabrique_article = None
    db = None
    cache = None
    depr_cache = ''

    # sections = {
    #     'LEGISCTA012345678901': (2, 'Titre II', 'De la loi', 1791-01-01, None, 2015-01-01, 2018-01-01, 'Titre II - De la loi\n\nArticle 3\n\nLes assujettis sont tenus d’aprendre la loi par cœur.\n\nArticle 4\n\nTout contrevenant aux dispositions de l’article 3 se voit remettre un 0/42 à l’examen de citoyenneté.')
    #     (string)(id): (
    #         (int >= 1)(numéro d’ordre dans la section parente),
    #         (string)(phrase correspondant au numéro d’ordre dans la section parente),
    #         (string)(titre de la section),
    #         (datetime.date)(date de début de vigueur de la section),
    #         (datetime.date|None)(date de fin de vigueur de la section),
    #         (datetime.date)(date de début de vigueur interne du cache de la section),
    #         (datetime.date|None)(date de fin de vigueur interne du cache de la section),
    #         (string)(cache de la section)
    #     )
    # }
    #
    # Le cache de la section correspond à la rédaction entre les dates de vigueur interne. On notera en effet que bien que la section a une période de vigueur relativement longue, son contenu change dès qu’un de ses composants internes change, c’est pour ce contenu spécifiquement que correspond les dates de vigueur internes.
    sections = {}

    def __init__( self, fabrique_article ):
        """
        :param fabrique_article:
            FabriqueArticle
        """
        self.fabrique_article = fabrique_article
        self.db = self.fabrique_article.db
        self.cache = self.fabrique_article.cache
        self.depr_cache = self.fabrique_article.depr_cache
        self.sections = {}

    def effacer_cache():
        self.sections = {}

    def obtenir_texte_section( self, niveau, id, debut_vigueur_texte, fin_vigueur_texte, etat_vigueur_section ):
        """
        Obtenir le texte d’une section donnée par un id.

        :param niveau:
            int - niveau (profondeur) de la section, commençant à 1 (i.e. l’ensemble du texte).
        :param id:
            string - ID de la section.
        :param debut_vigueur_texte:
            datetime.date - date de début de vigueur demandée.
        :param fin_vigueur_texte:
            datetime.date - date de fin de vigueur autorisée par la requête.
        :param etat_vigueur_section:
            string - état de la section
        :returns:
            (string, datetime.date, datetime.date, datetime.date) - (texte, debut_vigueur, fin_vigueur, fin_vigueur_interne) Texte de l’article, dates de début et fin de vigueur, fin de vigueur interne (plus proche future modification de la section).
        """

        texte = ''
        #debut_vigueur = None
        #fin_vigueur = None
        #debut_vigueur_interne = set()
        fins_vigueur = set()

        # Rédaction du titre - TODO abstraire ceci
        marque_niveau = ''
        for i in range(niveau):
            marque_niveau = marque_niveau + '#'

        # Obtenir les sections enfants
        sql_section_parente = "parent = '{0}'".format(id)
        if id == None:
            sql_section_parente = "parent IS NULL OR parent = ''"
        sections = self.db.all("""
            SELECT *
            FROM sommaires
            WHERE ({0})
              AND ({1})
            ORDER BY position
        """.format(sql_section_parente, sql))

        # Itérer sur les sections de cette section
        for section in sections:

            rcid, rparent, relement, rdebut, rfin, retat, rnum, rposition, r_source = section

            # date_debut ≤ date_debut_vigueur
            #if comp_infini_strict(debut_vigueur_texte, rdebut) or (comp_infini_strict(rfin, fin_vigueur_texte) and retat != 'VIGUEUR'):
            #    raise Exception(u'section non valide (version texte de {} a {}, version section de {} à {})'.format(debut_vigueur_texte, fin_vigueur_texte, rdebut, rfin))
            #    return texte

        # L’élément est un titre de sommaire, rechercher son texte et l’ajouter à la liste
        if relement[4:8] == 'SCTA':

            tsection = self.db.one("""
                SELECT titre_ta, commentaire
                FROM sections
                WHERE id='{0}'
            """.format(id))
            rarborescence = arborescence
            rarborescence.append( tsection[0].strip() )
            texte = self.obtenir_reer_sections(texte, niveau+1, relement, version_texte, sql, rarborescence, format, dossier, db, cache)

            texte = self.obtenir_texte_section( niveau+1, relement, debut_vigueur_texte, fin_vigueur_texte, retat )

            texte = texte                                  \
                    + marque_niveau + ' ' + tsection[0].strip() + '\n' \
                    + '\n'

        # L’élément est un article, l’ajouter à la liste
        elif relement[4:8] == 'ARTI':

            valeur_article = self.fabrique_article.obtenir_texte_article( niveau+1, relement, debut_vigueur_texte, fin_vigueur_texte, retat )

            texte_article, debut_vigueur_article, fin_vigueur_article = valeur_article

            if texte_article != None:
                texte = texte + texte_article
                # if debut_vigueur_texte < fin_vigueur_article
                if comp_infini_strict( debut_vigueur_texte, fin_vigueur_article ):
                    if fin_vigueur_article:
                        fins_vigueur.add( fin_vigueur_article )
            if comp_infini_strict( debut_vigueur_texte, debut_vigueur_article ):
                fins_vigueur.add( debut_vigueur_article )

        fin_vigueur = min( fins_vigueur )

        return texte, fin_vigueur

# vim: set ts=4 sw=4 sts=4 et:
