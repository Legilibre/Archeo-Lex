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
import subprocess
import re
import gitlab


def pousser_les_textes_sur_gitlab( textes, dossier, gitlab_host, gitlab_token, gitlab_group, git_server, git_key, calcules ):

    gl = gitlab.Gitlab(gitlab_host, private_token=gitlab_token)

    groupe = gl.groups.get( gitlab_group )
    separateur = ':'
    if '//' in git_server:
        separateur = '/'

    if calcules:
        f_calcules = open( calcules, 'a' )

    for texte in textes:
        print(texte)
        if texte == None: # TODO vérifier pourquoi certains valent None
            continue
        nom_gitlab = texte[1].replace('(', '').replace(')', '').replace(',', '.').replace("'", '’')
        adresse_gitlab = nom_gitlab.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('û', 'u').replace('ô', 'o').replace('’', '_')
        projet_gitlab = gl.projects.create( {'name': adresse_gitlab, 'namespace_id': groupe.id, 'visibility': 'public'} )
        projet_gitlab.jobs_enabled = False
        projet_gitlab.wiki_enabled = False
        projet_gitlab.issues_enabled = False
        projet_gitlab.snippets_enabled = False
        projet_gitlab.merge_requests_enabled = False
        projet_gitlab.shared_runners_enabled = False
        projet_gitlab.issues_requests_enabled = False
        projet_gitlab.name = nom_gitlab[0].upper() + nom_gitlab[1:].replace('_', ' ')
        projet_gitlab.tag_list = [ re.sub( r's([ -])', r'\1', texte[0].split('/')[0][0:-1] ) ]
        projet_gitlab.save()
        subprocess.call(['git', 'remote', 'add', 'origin', git_server+separateur+gitlab_group+'/'+adresse_gitlab], cwd=dossier+'/'+texte[0])
        r = subprocess.call(['git', 'push', '--all'], cwd=dossier+'/'+texte[0], env={'GIT_SSH_COMMAND': 'ssh -o "StrictHostKeyChecking no" -i '+git_key})
        if r != 0:
            gl.projects.delete( projet_gitlab.id )
            continue
        if f_calcules:
            f_calcules.write( texte[2] + ' ' + adresse_gitlab + '\n' )

    if f_calcules:
        f_calcules.close()

# vim: set ts=4 sw=4 sts=4 et:
