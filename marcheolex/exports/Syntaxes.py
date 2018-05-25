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


class Syntaxes:

    def transformer_depuis_html( self, html ):

        """
        Transformer un texte dans la syntaxe représentée à partir du HTML.

        :param html:
            (string) HTML à transformer.
        :returns:
            (string|None) Texte équivalent dans la syntaxe représentée.
        """

        raise NotImplementedError

    def ajouter_liens( self, texte, liens_internes, liens_externes ):

        """
        Ajouter des liens dans un texte.

        :param texte:
            (string) Texte où ajouter les liens.
        :param liens_internes:
            (dictionnaire string: string) Liste des liens internes à ajouter dans le texte.
        :param liens_externes:
            (dictionnaire string: string) Liste des liens externes à ajouter dans le texte.
        :returns:
            (string) Texte avec liens.
        """

        raise NotImplementedError

    def obtenir_titre( self, parents, texte ):

        """
        Obtenir le titre dans la syntaxe représentée.

        :param parents:
            (liste de strings) Niveaux parents de la ressource.
        :param texte:
            (string) Texte du titre.
        :returns:
            (string|None) Texte du titre dans la syntaxe représentée.
        """

        raise NotImplementedError


# vim: set ts=4 sw=4 sts=4 et:
