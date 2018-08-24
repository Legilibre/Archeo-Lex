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
import datetime
import time
from marcheolex.utilitaires import comp_infini_strict
from marcheolex.utilitaires import comp_infini_large
from marcheolex.exports import *

class FabriqueSection:

    fabrique_article = None
    db = None
    cache = None
    stockage = None
    syntaxe = None

    # sections = {
    #     'LEGISCTA012345678901': ('LEGISCTA123456789012', 2, 'Titre II', 'De la loi', 1791-01-01, None, 2015-01-01, 2018-01-01, 'Titre II - De la loi\n\nArticle 3\n\nLes assujettis sont tenus d’aprendre la loi par cœur.\n\nArticle 4\n\nTout contrevenant aux dispositions de l’article 3 se voit remettre un 0/42 à l’examen de citoyenneté.')
    #     (string)(id): (
    #         (string)(id de la section parente),
    #         (int >= 1)(numéro d’ordre dans la section parente),
    #         (string)(phrase correspondant au numéro d’ordre dans la section parente),
    #         (string)(titre de la section),
    #         (datetime.date|None)(date de début de vigueur de la section),
    #         (datetime.date|None)(date de fin de vigueur de la section),
    #         (datetime.date|None)(date de début de vigueur interne du cache de la section),
    #         (datetime.date|None)(date de fin de vigueur interne du cache de la section),
    #         (string|None)(cache de la section)
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
        self.stockage = fabrique_article.stockage
        self.syntaxe = fabrique_article.syntaxe

        self.sections = {}
        self.desactiver_cache = isinstance( self.stockage.organisation, UnArticleParFichierSansHierarchie ) or isinstance( self.stockage.organisation, UnArticleParFichierAvecHierarchie )


    def effacer_cache():

        self.sections = {}


    def obtenir_texte_section( self, id, hierarchie, cid, debut_vigueur_texte, fin_vigueur_texte ):

        """
        Obtenir le texte d’une section donnée par un id.

        :param id:
            string - ID de la section.
        :param hierarchie:
            [(str, str)] - Liste de couples (id, titre_ta) donnant le contexte dans la hiérarchie des titres.
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
        fins_vigueur = set()

        if 'texte' not in self.sections or self.sections['texte'] != cid:

            self.sections = {}

            sections = self.db.all("""
                SELECT sommaires.parent,
                       sommaires.element,
                       sommaires.debut,
                       sommaires.fin,
                       sommaires.num,
                       sommaires.position,
                       sections.titre_ta,
                       sections.commentaire,
                       sections.mtime
                FROM sommaires
                LEFT JOIN sections
                       ON sommaires.element = sections.id
                WHERE sommaires.cid = '{0}'
            """.format( cid ) )

            for section in sections:

                sparent, selement, sdebut, sfin, snum, sposition, stitre_ta, scommentaire, smtime = section

                sparent = sparent if sparent else None
                sdebut = datetime.date(*(time.strptime(sdebut, '%Y-%m-%d')[0:3])) if sdebut != '2999-01-01' else None
                sfin = datetime.date(*(time.strptime(sfin, '%Y-%m-%d')[0:3])) if sfin != '2999-01-01' else None

                if selement not in self.sections:
                    self.sections[selement] = {}
                self.sections[selement][sparent] = (sposition, snum, stitre_ta, sdebut, sfin, None, None, None)

            # Marquage de ce cache comme complet : il n’y a plus à le re-calculer
            self.sections['texte'] = cid

        sections = {}

        # Itérer sur les sections de cette section, le dictionnaire final servira ensuite à itérer dans l’ordre d’affichage des sections
        for section in self.sections:

            if section == 'texte' or id not in self.sections[section]:
                continue

            sfin = self.sections[section][id][4]
            sposition = self.sections[section][id][0]

            # La période de vigueur de cette section est expirée ou expire : ne pas l’ajouter au texte (sfin <= debut_vigueur_texte)
            # Le cas quasi-erroné où le texte n’a pas de début de vigueur est écarté ici, mais devrait probablement renvoyer une erreur ailleurs
            # TODO gérer le cas où debut_vigueur_texte == None (2 dans la base LEGI, à voir si AL trouve quand même des intervalles de vigueur)
            if debut_vigueur_texte and comp_infini_large( sfin, debut_vigueur_texte ):
                continue

            sections[sposition] = section

        # Itérer sur les sections non-expirées dans l’ordre d’affichage
        position = 0
        for i, section in sorted( sections.items() ):

            sposition, snum, stitre_ta, sdebut, sfin, cdebut, cfin, ctexte = self.sections[section][id]

            # Enregistrer la date de fin de vigueur de la section
            if sdebut != None and comp_infini_strict( debut_vigueur_texte, sdebut ):
                fins_vigueur.add( sdebut )
            if sfin != None and comp_infini_strict( debut_vigueur_texte, sfin ):
                fins_vigueur.add( sfin )

            # La période de vigueur de cette section n’est pas encore commencée (fin_vigueur_texte <= sdebut) 
            # Les sections intemporelles (= sans date de début de vigueur (et normalement sans date de fin de vigueur)) sont considérées comme toujours en vigueur
            if sdebut and comp_infini_large( fin_vigueur_texte, sdebut ):
                continue

            # Une des bornes de la période de vigueur de la section est strictement comprise dans l’intervalle courant de vigueur du texte : ce n’est pas censé arriver, les dates de changement de vigueur du texte sont censées être minimales
            if ( sdebut and comp_infini_strict( debut_vigueur_texte, sdebut ) ) or comp_infini_strict( sfin, fin_vigueur_texte ):
                raise Exception( 'Erreur interne : les intervalles de vigueur du texte sont être minimaux et il ne devrait donc pas exister une section avec une des bornes de vigueur strictement comprise dans l’intervalle courant de vigueur du texte' )

            position += 1
            # L’élément est un titre de sommaire, rechercher son texte et l’ajouter à la liste
            if section[4:8] == 'SCTA':

                chierarchie = hierarchie.copy()
                chierarchie.append( (position, section, stitre_ta) )

                # Le cache de section est valide et peut être utilisé pour ajouter le texte de la section
                # L’intervalle de vigueur du cache de sections comprend l’intervalle courant de vigueur du texte (cdebut <= debut_vigueur_texte and fin_vigueur_texte < cfin)
                # FIXME: pour les formats "articles" ou "sections", il faut désactiver ce "if" sinon certains fichier manquent, ajouter un paramètre ou autre mécanisme
                if not self.desactiver_cache and comp_infini_large( cdebut, debut_vigueur_texte ) and comp_infini_large( fin_vigueur_texte, cfin ):

                    texte = texte + ctexte

                    self.stockage.ecrire_ressource( section, chierarchie, snum, stitre_ta, ctexte )

                    # Si la section a une fin de vigueur, celle-ci devient une borne maximale de fin de vigueur des sections parentes
                    if cfin:
                        fins_vigueur.add( cfin )

                else:

                    if stitre_ta == None:
                        stitre_ta = '(sans titre)'

                    titre_formate = self.syntaxe.obtenir_titre( chierarchie, stitre_ta )
                    texte_section, fin_vigueur_section = self.obtenir_texte_section( section, chierarchie, cid, debut_vigueur_texte, fin_vigueur_texte )

                    snum = snum.strip() if snum else ''
                    texte_section = titre_formate + texte_section
                    texte = texte + texte_section

                    self.stockage.ecrire_ressource( section, chierarchie, snum, stitre_ta, texte_section )

                    self.sections[section][id] = (sposition, snum, stitre_ta, sdebut, sfin, debut_vigueur_texte, fin_vigueur_section, texte_section)

                    # Si la section a une fin de vigueur, celle-ci devient une borne maximale de fin de vigueur des sections parentes
                    if fin_vigueur_section:
                        fins_vigueur.add( fin_vigueur_section )

            # L’élément est un article, l’ajouter à la liste
            elif section[4:8] == 'ARTI':

                chierarchie = hierarchie.copy()
                chierarchie.append( (position, section, None) )

                valeur_article = self.fabrique_article.obtenir_texte_article( section, chierarchie, debut_vigueur_texte, fin_vigueur_texte )

                num, texte_article, debut_vigueur_article, fin_vigueur_article = valeur_article

                # L’article a une période de vigueur comprise dans l’intervalle courant de vigueur du texte : ajouter le texte
                if texte_article != None:
                    
                    texte = texte + texte_article

                    # Si l’article a une fin de vigueur, celle-ci devient une borne maximale de fin de vigueur des sections parentes
                    if fin_vigueur_article:
                        fins_vigueur.add( fin_vigueur_article )

                # Si l’article a un début de vigueur après l’intervalle courant de vigueur du texte,
                #   celle-ci devient une borne maximale de vigueur des sections parentes (debut_vigueur_texte < debut_vigueur_article)
                if comp_infini_strict( debut_vigueur_texte, debut_vigueur_article ) and debut_vigueur_article:
                    fins_vigueur.add( debut_vigueur_article )

        fin_vigueur = None
        if len( fins_vigueur ):
            fin_vigueur = min( fins_vigueur )

        return texte, fin_vigueur

# vim: set ts=4 sw=4 sts=4 et:
