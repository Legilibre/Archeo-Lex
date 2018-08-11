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


class Stockage:

    def __init__( self, organisation ):

        """
        Initialisation.

        :param organisation:
            (Organisations) Classe implémentant une certaine organisation des fichiers, par exemple un fichier unique ou un article par fichier.
        :returns:
            (None)
        """

        self.organisation = organisation

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

        raise NotImplementedError

    def ecrire_texte( self ):

        """
        Écrire le fichier la version du texte.
        """

        raise NotImplementedError


# vim: set ts=4 sw=4 sts=4 et:
