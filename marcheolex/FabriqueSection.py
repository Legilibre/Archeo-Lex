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
    stockage = None

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
        self.stockage = fabrique_article.stockage
        self.sections = {}


    def effacer_cache():

        self.sections = {}


    def obtenir_texte_section( self, niveau, id, cid, debut_vigueur_texte, fin_vigueur_texte ):

        """
        Obtenir le texte d’une section donnée par un id.

        :param niveau:
            int - niveau (profondeur) de la section, commençant à 1 (i.e. l’ensemble du texte).
        :param id:
            string - ID de la section.
        :param cid:
            string - CID du texte.
        :param debut_vigueur_texte:
            datetime.date - date de début de vigueur demandée.
        :param fin_vigueur_texte:
            datetime.date - date de fin de vigueur autorisée par la requête.
        :returns:
            (string, datetime.date) - (texte, fin_vigueur) Texte de l’article, date de fin de vigueur interne (plus proche future modification de la section).
        """

        texte = ''
        #debut_vigueur = None
        #fin_vigueur = None
        #debut_vigueur_interne = set()
        fins_vigueur = set()

        # Obtenir les sections enfants
        sql_section_parente = "parent = '{0}'".format(id)
        if id == None:
            sql_section_parente = "parent IS NULL OR parent = ''"
        sections = self.db.all("""
            SELECT *
            FROM sommaires
            WHERE cid = '{0}'
              AND ( debut <= '{1}' OR debut == '2999-01-01' )
              {2}
              AND ({3})
            ORDER BY position
        """.format( cid, debut_vigueur_texte, "AND ( fin >= '{0}' OR fin == '2999-01-01' OR etat == 'VIGUEUR' )".format( fin_vigueur_texte ) if fin_vigueur_texte else '', sql_section_parente))

        # Itérer sur les sections de cette section
        for section in sections:

            rcid, rparent, relement, rdebut, rfin, retat, rnum, rposition, r_source = section

            # L’élément est un titre de sommaire, rechercher son texte et l’ajouter à la liste
            if relement[4:8] == 'SCTA':

                #if rfin < debut_vigueur_texte:
                if comp_infini_strict( rfin, debut_vigueur_texte ):
                    continue

                #if rdebut > fin_vigueur_texte:
                if comp_infini_strict( fin_vigueur_texte, rdebut ):
                    continue

                # if debut_vigueur_texte < debut_vigueur_section
                if comp_infini_strict( debut_vigueur_texte, rdebut ):
                    if rdebut:
                        fins_vigueur.add( rdebut )
                    continue

                if relement not in self.sections:

                    tsection = self.db.one("""
                        SELECT titre_ta, commentaire
                        FROM sections
                        WHERE id='{0}'
                    """.format(relement))
                    titre_ta, commentaire = tsection

                    if rdebut == '2999-01-01':
                        rdebut = None
                    else:
                        rdebut = datetime.date(*(time.strptime(rdebut, '%Y-%m-%d')[0:3]))

                    if rfin == '2999-01-01':
                        rfin = None
                    else:
                        rfin = datetime.date(*(time.strptime(rfin, '%Y-%m-%d')[0:3]))

                    self.sections[relement] = (rnum, rnum, titre_ta, rdebut, rfin, None, None, None)

                #if debut_vigueur_texte >= self.section[id][5] and fin_vigueur_texte < self.section[id][6]
                if comp_infini_large( self.sections[relement][6], debut_vigueur_texte ) and comp_infini_strict( fin_vigueur_texte, self.sections[relement][7] ):
                    texte = texte + self.sections[relement][5]
                    if self.sections[relement][7]:
                        fins_vigueur.add( self.sections[relement][7] )

                else:
                    niveaux = [ False ] * (niveau+1)
                    texte_titre_ta = self.stockage.ecrire_ressource( relement, niveaux, rnum.strip() if rnum else '', self.sections[relement][2], '' )
                    valeur_section = self.obtenir_texte_section( niveau+1, relement, cid, debut_vigueur_texte, fin_vigueur_texte )
                    texte_section, fin_vigueur_section = valeur_section
                    texte_section = texte_titre_ta + texte_section

                    rnum, rnum, titre_ta, rdebut, rfin, _, _, _ = self.sections[relement]
                    self.sections[relement] = (rnum, rnum, titre_ta, rdebut, rfin, texte_section, debut_vigueur_texte, fin_vigueur_section)
                    texte = texte + texte_section
                    if fin_vigueur_section:
                        fins_vigueur.add( fin_vigueur_section )

            # L’élément est un article, l’ajouter à la liste
            elif relement[4:8] == 'ARTI':

                valeur_article = self.fabrique_article.obtenir_texte_article( niveau+1, relement, debut_vigueur_texte, fin_vigueur_texte, retat )

                num, texte_article, debut_vigueur_article, fin_vigueur_article = valeur_article

                if texte_article != None:
                    texte = texte + texte_article
                    if fin_vigueur_article:
                        fins_vigueur.add( fin_vigueur_article )
                # if debut_vigueur_texte < debut_vigueur_article
                if comp_infini_strict( debut_vigueur_texte, debut_vigueur_article ) and debut_vigueur_article:
                    fins_vigueur.add( debut_vigueur_article )

        fin_vigueur = None
        if len( fins_vigueur ):
            fin_vigueur = min( fins_vigueur )

        return texte, fin_vigueur

# vim: set ts=4 sw=4 sts=4 et:
