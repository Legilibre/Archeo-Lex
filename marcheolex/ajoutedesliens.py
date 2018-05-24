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
import re


def ajoute_liens( texte ):

        """
        Rechercher des liens dans un texte.

        :param texte:
            (string) Texte où seront ajouté les liens.
        :returns:
            (liste de tuples) Chaque tuple comprend : le texte de la capture, puis les parties d’identification.
        """

        liens = []

        # Constitution (en vigueur à la date du texte)
        results = re.findall( r'(articles? *([0-9.\-a-z]+)) de la constitution', texte, re.IGNORECASE )
        for result in results:
            liens.append( ( result[0], 'constitution', 'article '+result[2] ) )

        # Présente loi
        results = re.findall( r'(article *([0-9]+ ?[a-z]* ?[A-Z]*)) de la( présente)? loi', texte )
        for result in results:
            liens.append( ( result[0], 'présente loi', 'article '+result[2] ) )

        return liens

# vim: set ts=4 sw=4 sts=4 et:
