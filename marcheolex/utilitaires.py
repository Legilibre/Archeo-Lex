# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module comprend diverses fonctions utilitaires
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
import re
import subprocess
import datetime
from path import path

MOIS = {
    'janvier': '01',
    'février': '02',
    'mars': '03',
    'avril': '04',
    'mai': '05',
    'juin': '06',
    'juillet': '07',
    'août': '08',
    'septembre': '09',
    'octobre': '10',
    'novembre': '11',
    'décembre': '12'
}


MOIS2 = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']


def telecharger(url, fichier):
    
    subprocess.call(['wget', '--output-document=' + fichier, url])


def telecharger_cache(url, fichier, force=False):
    
    if os.path.exists(fichier):
        touch = datetime.datetime.fromtimestamp(os.stat(fichier).st_mtime)
        delta = datetime.datetime.today() - touch
        
        if not force or not isinstance(force, bool) and isinstance(force, (int, long, float)) and delta.total_seconds() < force:
            print('* Téléchargement de ' + url + ' (cache)')
            return True
    
    print('* Téléchargement de ' + url)
    return telecharger(url, fichier)


def normalisation_code(code):
    
    nom = ''
    repertoire = ''
    
    if code.startswith('code') or code.startswith('Code'):
        code = re.sub('\'', '’', code.lower())
        nom = re.sub('[-_]', ' ', code)
        nom = nom[0].upper() + nom[1:]
        repertoire = re.sub('[ _]', '-', code)
        nom = re.sub(' ', '_', re.sub('é', 'e', nom))
    else:
        nom = code.lower()
        repertoire = code.lower()
    
    return repertoire, nom


def normalise_date(texte):
    
    texte = texte.strip()
    if texte == '2999-01-01' or not texte:
        return None
    fm = re.match('(\d{4})-(\d{2})-(\d{2})', texte)
    if not fm:
        return None
    return datetime.date(int(fm.group(1)), int(fm.group(2)), int(fm.group(3)))


def normalise_datetime(texte):
    
    texte = texte.strip()
    fm = re.match('(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})', texte)
    if not fm:
        return None
    return datetime.datetime(int(fm.group(1)), int(fm.group(2)), int(fm.group(3)), int(fm.group(4)), int(fm.group(5)), int(fm.group(6)))


def chemin_texte(cidTexte, code=True, vigueur=True):
    
    if vigueur:
        vigueur = 'en'
    else:
        vigueur = 'non'
    
    if code:
        code = 'code'
    else:
        code = 'TNC'
    
    return os.path.join('legi', 'global', 'code_et_TNC_' + vigueur + '_vigueur', code + '_' + vigueur + '_vigueur', decompose_cid(cidTexte))


def decompose_cid(cidTexte):
    
    FFFF = cidTexte[0:4]
    TTTT = cidTexte[4:8]
    xx1 = cidTexte[8:10]
    xx2 = cidTexte[10:12]
    xx3 = cidTexte[12:14]
    xx4 = cidTexte[14:16]
    xx5 = cidTexte[16:18]
    
    return os.path.join(FFFF, TTTT, xx1, xx2, xx3, xx4, xx5, cidTexte)


#  x   y  résultat
#  ∞   ∞   0
#  ∞   N   1
#  N   ∞  -1
#  N  N+1 -1
# N+1  N   1
#  N   N   0
def comp_infini(x, y):
    
    if x == y:
        return 0
    if x == None:
        return 1
    if y == None:
        return -1
    return -2 * int(x < y) + 1


#  x   y  résultat
#  ∞   ∞  False
#  ∞   N  False
#  N   ∞  True
#  N  N+1 True
# N+1  N  False
#  N   N  False
def comp_infini_strict(x, y):
    
    if x == None and y == None:
        return False
    if x == None:
        return False
    if y == None:
        return True
    return x < y


#  x   y  résultat
#  ∞   ∞  True
#  ∞   N  False
#  N   ∞  True
#  N  N+1 True
# N+1  N  False
#  N   N  True
def comp_infini_large(x, y):
    
    if x == y:
        return True
    if x == None:
        return False
    if y == None:
        return True
    return x < y


def nop():
    
    return


def verif_taille(taille, destination):
    
    s = os.statvfs(destination)
    
    if 1.05 * taille >= s.f_bavail * s.f_frsize:  # en octets
        return False
    else:
        return True

