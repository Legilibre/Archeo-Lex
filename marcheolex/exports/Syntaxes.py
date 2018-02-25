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
