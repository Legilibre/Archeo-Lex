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
import time
import shutil
from path import Path

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
    
    if code.startswith(('code', 'Code')):
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
    
    if cidTexte[0:4] == 'LEGI':

        if vigueur:
            vigueur = 'en'
        else:
            vigueur = 'non'
    
        if code:
            code = 'code'
        else:
            code = 'TNC'
    
        return os.path.join('legi', 'global', 'code_et_TNC_' + vigueur + '_vigueur', code + '_' + vigueur + '_vigueur', decompose_cid(cidTexte))

    else:

        return os.path.join(cidTexte[0:4].lower(), 'global', decompose_cid(cidTexte))


def decompose_cid(cidTexte):
    
    FFFF = cidTexte[0:4]
    TTTT = cidTexte[4:8]
    xx1 = cidTexte[8:10]
    xx2 = cidTexte[10:12]
    xx3 = cidTexte[12:14]
    xx4 = cidTexte[14:16]
    xx5 = cidTexte[16:18]
    
    return os.path.join(FFFF, TTTT, xx1, xx2, xx3, xx4, xx5, cidTexte)


def obtenir_tous_textes(base, cache, code=True, vigueur=True):

    dir_base = os.path.join(cache, 'bases-xml', base.lower(), 'global')
    if base == 'LEGI':
        if vigueur:
            vigueur = 'en'
        else:
            vigueur = 'non'

        if code:
            code = 'code'
        else:
            code = 'TNC'

        dir_base = os.path.join(dir_base, 'code_et_TNC_' + vigueur + '_vigueur', code + '_' + vigueur + '_vigueur')

    result = explorer_textes(dir_base)

    result2 = []
    for d in result:
        result2.append((None,d,None,None))

    return result2

def explorer_textes(dir_base):

    list_dir = os.listdir(dir_base)
    result = []
    for d in list_dir:
        if re.match('[a-zA-Z]{4}TEXT[0-9]{12}\\.xml', d):
            result.append(d[0:20])
        else:
            result = result + explorer_textes(os.path.join(dir_base, d))
    return result

def comp_infini(x, y):
    
    dateinf = datetime.date(2999, 1, 1)

    if isinstance(x, basestring):
        x = datetime.date(*(time.strptime(x, '%Y-%m-%d')[0:3]))
    if isinstance(y, basestring):
        y = datetime.date(*(time.strptime(y, '%Y-%m-%d')[0:3]))
    if x == dateinf:
        x = None
    if y == dateinf:
        y = None

    if x == y:
        return 0;
    elif x == None:
        return 1
    elif y == None:
        return -1
    return -2 * int(x < y) + 1


def comp_infini_strict(x, y):
    
    dateinf = datetime.date(2999, 1, 1)

    if isinstance(x, basestring):
        x = datetime.date(*(time.strptime(x, '%Y-%m-%d')[0:3]))
    if isinstance(y, basestring):
        y = datetime.date(*(time.strptime(y, '%Y-%m-%d')[0:3]))
    if x == dateinf:
        x = None
    if y == dateinf:
        y = None

    if x == None and y == None:
        return False
    elif x == None:
        return False
    elif y == None:
        return True
    return x < y


def comp_infini_large(x, y):
    
    dateinf = datetime.date(2999, 1, 1)

    if isinstance(x, basestring):
        x = datetime.date(*(time.strptime(x, '%Y-%m-%d')[0:3]))
    if isinstance(y, basestring):
        y = datetime.date(*(time.strptime(y, '%Y-%m-%d')[0:3]))
    if x == dateinf:
        x = None
    if y == dateinf:
        y = None

    if x == y:
        return True
    elif x == None:
        return False
    elif y == None:
        return True
    return x < y


def min_date_infini( x, y ):

    if x == None:
        return y
    elif y == None:
        return x
    elif x < y:
        return x
    return y


def nop():
    
    return


def verif_taille(taille, destination):
    
    s = os.statvfs(destination)
    
    if 1.05 * taille >= s.f_bavail * s.f_frsize:  # en octets
        return False
    else:
        return True


def fusionner(root_src_dir, root_dst_dir):

    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)
    shutil.rmtree(root_src_dir)

# vim: set ts=4 sw=4 sts=4 et:
