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
from . import Organisations
from . import Syntaxes


class UnArticleParFichierSansHierarchie( Organisations ):

    """
    Les articles sont écrits à raison d’un fichier par article sous le nom 'Article_%numéro%'.
    """

    def __init__( self, extension ):

        """
        Initialisation.

        :param extension:
            (str) Extension du fichier.
        :returns:
            (None)
        """

        self.extension = '.' + extension if extension else ''

    def obtenir_nom_fichier( self, id, parents, num, titre ):

        """
        Obtenir le nom du fichier où écrire la ressource donnée en paramètres.

        :param id:
            (string) ID de la ressource.
        :param parents:
            (liste de strings) Niveaux parents de la ressource.
        :param num:
            (string) Numéro de la ressource par rapport aux autres de même niveau.
        :param titre:
            (string) Titre de la ressource.
        :returns:
            (string|None) Emplacement du fichier ou None pour ne pas écrire la ressource.
        """

        if id[4:8] == 'ARTI':
            if num:
                return 'Article_' + num + self.extension
            else:
                return 'Article_' + id + self.extension

        return None

    def ecrire_ressource( self, id, parents, num, titre, texte ):

        """
        :param id:
            (string) ID de la ressource.
        :param parents:
            (liste de strings) Niveaux parents de la ressource.
        :param num:
            (string) Numéro de la ressource par rapport aux autres de même niveau.
        :param titre:
            (string) Titre de la ressource.
        :param texte:
            (string|None) Texte de la ressource.
        :returns:
            (list((str|None,str))) Liste de fichiers et texte de la ressource.
        """

        nom_fichier = self.obtenir_nom_fichier( id, parents, num, titre )

        if nom_fichier:
            return [(nom_fichier, texte)]
        return []


# vim: set ts=4 sw=4 sts=4 et:
