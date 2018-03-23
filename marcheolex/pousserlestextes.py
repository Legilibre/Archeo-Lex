# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – ce module pousse les dépôts sur Gitlab
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
import os
import subprocess
import datetime
import time
import re
from pytz import timezone
from string import strip, join
from path import Path
from bs4 import BeautifulSoup
import legi
import legi.utils
import gitlab
from marcheolex import logger
from marcheolex import version_archeolex
from marcheolex import natures
from marcheolex.markdownlegi import creer_markdown
from marcheolex.markdownlegi import creer_markdown_texte
from marcheolex.utilitaires import normalisation_code
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import nop
from marcheolex.utilitaires import MOIS
from marcheolex.utilitaires import MOIS2
from marcheolex.utilitaires import comp_infini
from marcheolex.utilitaires import comp_infini_strict


def pousser_les_textes_sur_gitlab( textes, dossier, gitlab_host, gitlab_token, gitlab_group, git_server, git_port, git_key ):

    gl = gitlab.Gitlab(gitlab_host, private_token=gitlab_token)

    groupe = gl.groups.get( gitlab_group )
    if git_port:
        git_port = ':' + git_port + '/'
    else:
        git_port = ':'

    for texte in textes:
        print(texte)
        if texte == None: # TODO vérifier pourquoi certains valent None
            continue
        nom_gitlab = texte[1].replace('é', 'e').replace('è', 'e').replace('ê', 'e')
        gl.projects.create( {'name': texte[1], 'namespace_id': groupe.id, 'visibility': 'public'} )
        subprocess.call(['git', 'remote', 'add', 'origin', git_server+git_port+gitlab_group+'/'+nom_gitlab], cwd=dossier+'/'+texte[0])
        subprocess.call(['git', 'push', '--all'], cwd=dossier+'/'+texte[0], env={'GIT_SSH_COMMAND': 'ssh -i '+git_key})

# vim: set ts=4 sw=4 sts=4 et:
