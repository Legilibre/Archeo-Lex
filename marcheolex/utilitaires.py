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
import ftplib
import string
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


def comp_infini(x, y):
    
    if x == y:
        return 0
    if x == None:
        return 1
    if y == None:
        return -1
    return -2 * int(x < y) + 1


def comp_infini_strict(x, y):
    
    if x == None and y == None:
        return False
    if x == None:
        return False
    if y == None:
        return True
    return x < y


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


# Téléchargement des bases juridiques
# 
# @param str identifiant 'JORF', 'LEGI', 'KALI', 'CNIL', 'CONSTIT', 'CIRCULAIRES'
# @param str/int/None date_maj None pour télécharger toute la base
#                              Pour la plus récente mise à jour avant une certaine date, utiliser 'AAAAMMJJ[-HHMMSS]', par exemple '29990101' (clin d’œil)
#                              Pour la dernière, avant-dernière, etc. mise à jour, utiliser '0', '-1', etc. (ou 0, -1, etc.)
# @param str cache
# 
# Voici des exemples d’URLs :
# - ftp://jorf:open1234@ftp2.journal-officiel.gouv.fr/LicenceFreemium_jorf_jorf_global_20140718-104554.tar.gz
# - ftp://legi:open1234@ftp2.journal-officiel.gouv.fr/LicenceFreemium_legi_legi_global_20140718-113010.tar.gz
# - ftp://kali:open1234@ftp2.journal-officiel.gouv.fr/LicenceFreemium_kali_kali__20140718-142314.tar.gz
# - ftp://cnil:open1234@ftp2.journal-officiel.gouv.fr/LicenceFreemium_CNIL_cnil_global_20140718-104251.tar.gz
# - ftp://constit:open1234@ftp2.journal-officiel.gouv.fr/LicenceFreemium_CONSTIT_constit_global_20140718-104144.tar.gz
# - ftp://anonymous:@echanges.dila.gouv.fr:6370/CIRCULAIRES/ (non-testé, très probablement non-fonctionnel)
# Voir http://rip.journal-officiel.gouv.fr/index.php/pages/juridiques
def telecharger_base(identifiant, date_maj, cache):
    
    identifiant = identifiant.upper()
    if identifiant not in ['JORF', 'LEGI', 'KALI', 'CNIL', 'CONSTIT']:
        raise Exception()
    if isinstance(date_maj, int):
        date_maj = str(date_maj)
    elif not isinstance(date_maj, str) and not date_maj == None:
        raise Exception()
    path(os.path.join(cache, 'tar')).mkdir_p()
    
    serveur = {
        'JORF': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'jorf', 'open1234'),
        'LEGI': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'legi', 'open1234'),
        'KALI': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'kali', 'open1234'),
        'CNIL': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'cnil', 'open1234'),
        'CONSTIT': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'constit', 'open1234'),
        'CIRCULAIRES': ('ftp', 'echanges.dila.gouv.fr:6370/CIRCULAIRES/', 'anonymous', ''),
    }
    fichier_base = {
        'JORF': 'LicenceFreemium_jorf_jorf_global_%Y%m%d-%H%M%S.tar.gz',
        'LEGI': 'LicenceFreemium_legi_legi_global_%Y%m%d-%H%M%S.tar.gz',
        'KALI': 'LicenceFreemium_kali_kali__%Y%m%d-%H%M%S.tar.gz',
        'CNIL': 'LicenceFreemium_CNIL_cnil_global_%Y%m%d-%H%M%S.tar.gz',
        'CONSTIT': 'LicenceFreemium_CONSTIT_constit_global_%Y%m%d-%H%M%S.tar.gz',
        'CIRCULAIRES': ''
    }
    fichier_majo = {
        'JORF': 'jorf_%Y%m%d-%H%M%S.tar.gz',
        'LEGI': 'legi_%Y%m%d-%H%M%S.tar.gz',
        'KALI': 'kali_%Y%m%d-%H%M%S.tar.gz',
        'CNIL': 'cnil_%Y%m%d-%H%M%S.tar.gz',
        'CONSTIT': 'constit_%Y%m%d-%H%M%S.tar.gz',
        'CIRCULAIRES': ''
    }
    
    # Connexion FTP
    connexion_ftp = ftplib.FTP(serveur[identifiant][1], serveur[identifiant][2], serveur[identifiant][3])
    liste_fichiers = connexion_ftp.nlst()
    
    # Recherche du fichier le plus récent et toutefois antérieure à la date demandée
    if date_maj == None:
        prefixe = string.split(fichier_base[identifiant], '%')[0]
        type_fichier = 'base'
    else:
        prefixe = string.split(fichier_majo[identifiant], '%')[0]
        type_fichier = 'majo'
    dates = []
    for fichier in liste_fichiers:
        if fichier.startswith(prefixe):
            dates.append(re.sub(prefixe + '([0-9-]+)\.tar\.gz', r'\1', fichier))
    dates.sort(None, None, True)
    date_selectionnee = 0
    if date_maj:
        if len(date_maj) == 8:
            date_maj = date_maj + '-235959'
        if re.match('^(0|-\d+)$', date_maj):
            date_selectionnee = -int(date_maj)
        else:
            while date_selectionnee < len(dates) and dates[date_selectionnee] > date_maj:
                date_selectionnee = date_selectionnee + 1
            if date_selectionnee == len(dates):
                raise Exception()
    recent = dates[date_selectionnee]
    
    # Création de l’URL
    url = serveur[identifiant][0] + '://' + serveur[identifiant][2] + ':' + serveur[identifiant][3] + '@' + serveur[identifiant][1] + '/' + prefixe + recent + '.tar.gz'
    
    # Vérification de la taille disponible
    if not verif_taille(connexion_ftp.size(prefixe + recent + '.tar.gz'), cache) and not os.path.exists(identifiant + '-' + type_fichier + '-' + recent + '.tar.gz'):
        raise Exception()
    connexion_ftp.close()
    
    # Téléchargement de la base demandée
    return telecharger_cache(url, os.path.join(cache, 'tar', identifiant + '-' + type_fichier + '-' + recent + '.tar.gz'))

