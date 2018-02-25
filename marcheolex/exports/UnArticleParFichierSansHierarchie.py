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
from . import Organisations
from . import Syntaxes


class UnArticleParFichierSansHierarchie( Organisations ):

    """
    Les articles sont écrits à raison d’un fichier par article sous le nom 'Article_%numéro%'.
    """

    extension = ''

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
            (string) Texte de la ressource.
        """

        if not self.syntaxe:
            raise Exception()

        texte = ''
        if id[4:8] == 'ARTI':
            if num:
                titre = 'Article ' + num
            else:
                titre = 'Article (non-numéroté)'
            titre_formate = self.syntaxe.obtenir_titre( parents, titre )
            texte = texte + titre_formate + texte + '\n\n'
        elif id[4:8] == 'SCTA':
            titre_formate = self.syntaxe.obtenir_titre( parents, titre )
            texte = texte + titre_formate + '\n\n'
        else:
            raise Exception()

        return texte

    def ecrire_texte( self ):

        """
        Écrire le fichier la version du texte.
        """

        pass


# vim: set ts=4 sw=4 sts=4 et:
