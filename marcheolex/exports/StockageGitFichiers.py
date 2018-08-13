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
import os
import subprocess
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
            (None)
        """

        fichiers = self.organisation.ecrire_ressource( id, parents, num, titre, texte )

        # Enregistrer les fichiers
        for fichier in fichiers:
            with open( os.path.join( self.dossier, fichier[0] ), 'w' ) as f:
                contenu = fichier[1].strip()
                if contenu:
                    f.write( fichier[1].strip() + '\n' )
                else:
                    f.write( '' )


    def ecrire_texte( self, id, titre, texte ):

        """
        Écrire le fichier la version du texte.

        :param id:
            (string) ID de la ressource.
        :param titre:
            (string) Titre de la ressource.
        :param texte:
            (string|None) Texte de la ressource.
        :returns:
            (None)
        """

        fichiers = self.organisation.ecrire_texte( id, titre, texte )

        # Enregistrer les fichiers
        for fichier in fichiers:
            with open( os.path.join( dossier, fichier[0] ), 'w' ) as f:
                contenu = fichier[1].strip()
                if contenu:
                    f.write( fichier[1].strip() + '\n' )
                else:
                    f.write( '' )

        # Ajouter les fichiers dans Git
        subprocess.call(['git', 'add', '.'], cwd=self.dossier)


# vim: set ts=4 sw=4 sts=4 et:
