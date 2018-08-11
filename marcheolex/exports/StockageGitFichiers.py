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
from . import Stockage
from . import UnArticleParFichierSansHierarchie
from . import FichierUnique


class StockageGitFichiers( Stockage ):

    def ecrire_ressource( self, id, parents, num, titre, texte ):

        """
        Écrire la ressource en cours.

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
            (string) Texte de la ressource.
        """

        texte_retourne = self.organisation.ecrire_ressource( id, parents, num, titre, texte )

        if isinstance( self.organisation, UnArticleParFichierSansHierarchie ):
            nom_fichier = self.organisation.obtenir_nom_fichier( id, parents, num, titre )
            if nom_fichier:
                f_texte = open( nom_fichier, 'w' )
                f_texte.write( texte + '\n' )
                f_texte.close()

        return texte_retourne


    def ecrire_texte( self ):

        """
        Écrire le fichier la version du texte.
        """

        if isinstance( self.organisation, FichierUnique ):
            nom_fichier = self.organisation.obtenir_nom_fichier( None, None, None, None )
            texte = self.organisation.texte.strip() + '\n'
            f_texte = open( nom_fichier, 'w' )
            f_texte.write( texte )
            f_texte.close()


# vim: set ts=4 sw=4 sts=4 et:
