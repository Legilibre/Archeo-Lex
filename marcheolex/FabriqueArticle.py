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
from marcheolex.utilitaires import comp_infini_large
from marcheolex.exports import *

class FabriqueArticle:

    def __init__( self, db, stockage, syntaxe, cache = None ):

        """
        :param db:
            Base de donnée.
        :param stockage:
            (Stockage) Classe modélisant le stockage.
        :param syntaxe:
            (Syntaxes) Classe modélisant la syntaxe.
        :param cache:
            boolean Utilisation d’un cache mémoire
        """

        self.db = db
        self.stockage = stockage
        self.syntaxe = syntaxe
        self.cache = cache

        self.articles = {}
        self.erreurs = []


    def effacer_cache(self):

        self.articles = {}


    def obtenir_texte_article( self, id, hierarchie, debut_vigueur_texte, fin_vigueur_texte ):

        """
        Obtenir le texte d’un article donné par un id.

        :param id:
            string - ID de l’article.
        :param hierarchie:
            [(str, str)] - Liste de couples (id, titre_ta) donnant le contexte dans la hiérarchie des titres.
        :param debut_vigueur_texte:
            datetime.date - date de début de vigueur demandée.
        :param fin_vigueur_texte:
            datetime.date - date de fin de vigueur autorisée par la requête.
        :returns:
            (string, string, datetime.date, datetime.date) - (num, texte, debut_vigueur, fin_vigueur) Numéro et texte de l’article, dates de début et fin de vigueur.
        """

        if id not in self.articles:

            article = self.db.one("""
                SELECT num, date_debut, date_fin, bloc_textuel, cid
                FROM articles
                WHERE id = '{0}'
            """.format(id))
            if not article:
                article = self.db.one("""
                    SELECT num, debut, fin
                    FROM sommaires
                    WHERE element = '{0}'
                """.format(id))
                if not article:
                    self._cache_article( id, 'INCONNU', None, None, '(article manquant)' )
                    self.erreurs.append( 'Article {0} inconnu (métadonnées inconnues)'.format(id) )
                else:
                    num, date_debut, date_fin = article
                    self._cache_article( id, num, date_debut, date_fin, '(article manquant)' )
                    self.articles[id] = (num, '(article manquant)', None, None )
                    self.erreurs.append( 'Article {0} inconnu (métadonnées connues : numéro={1}, date_debut={2}, date_fin={3})'.format(id, num, date_debut, date_fin) )
            else:
                num, date_debut, date_fin, bloc_textuel, cid = article

                articles = self.db.all("""
                    SELECT id, num, date_debut, date_fin, bloc_textuel
                    FROM articles
                    WHERE cid = '{0}'
                """.format(cid))

                for article in articles:

                    aid, num, date_debut, date_fin, bloc_textuel = article

                    self._cache_article( aid, num, date_debut, date_fin, bloc_textuel )

        num, texte_article, date_debut, date_fin = self.articles[id]

        # La période de vigueur de cet article est expiré ou expire : ne pas l’ajouter au texte (date_fin <= debut_vigueur_texte)
        # Le cas quasi-erroné où le texte n’a pas de début de vigueur est écarté ici, mais devrait probablement renvoyer une erreur ailleurs
        if debut_vigueur_texte and comp_infini_large( date_fin, debut_vigueur_texte ):
            return (num, None, date_debut, date_fin)

        # La période de vigueur de cet article n’est pas encore commencé (fin_vigueur_texte <= date_debut) 
        # Les articles intemporels (= sans date de début de vigueur (et normalement sans date de fin de vigueur)) sont considérés comme toujours en vigueur
        if date_debut and comp_infini_large( fin_vigueur_texte, date_debut ):
            return (num, None, date_debut, date_fin)

        if not self.cache:
            self.effacer_cache()

        # Assemblage du texte
        num = num.strip() if num else ''
        texte_article = texte_article.strip()
        titre = 'Article ' + num if num else 'Article (non-numéroté)'
        hierarchie[-1] = (hierarchie[-1][0], id, titre)
        titre_formate = self.syntaxe.obtenir_titre( hierarchie, titre )
        texte_retourne = titre_formate + texte_article + '\n\n'

        # Enregistrement
        self.stockage.ecrire_ressource( id, hierarchie, num, '', texte_article )

        return (num, texte_retourne, date_debut, date_fin)

    def _cache_article( self, id, num, date_debut, date_fin, bloc_textuel ):

        """
        Fonction interne d’enregistrement dans le cache d’un article issu de la base de données.

        :param id:
            (str) ID de l’article.
        :param num:
            (str) Numéro de l’article.
        :param date_debut:
            (str) Date de début de vigueur demandée.
        :param date_fin:
            (str) Date de fin de vigueur autorisée par la requête.
        :param bloc_textuel:
            (str) Corps de l’article (en HTML).
        :returns:
            (None)
        """

        num = num.strip() if isinstance( num, str ) else ''

        date_debut = datetime.date(*(time.strptime(date_debut, '%Y-%m-%d')[0:3])) if date_debut != '2999-01-01' else None
        date_fin = datetime.date(*(time.strptime(date_fin, '%Y-%m-%d')[0:3])) if date_fin != '2999-01-01' else None

        texte_article = self.syntaxe.transformer_depuis_html( bloc_textuel )

        self.articles[id] = (num, texte_article, date_debut, date_fin)

# vim: set ts=4 sw=4 sts=4 et:
