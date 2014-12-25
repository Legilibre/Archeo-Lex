# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module télécharge diverses donnés et métadonnées depuis Légifrance
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
import string
import ftplib
from datetime import datetime
from path import path
from bs4 import BeautifulSoup
from marcheolex.utilitaires import telecharger
from marcheolex.utilitaires import telecharger_cache
from marcheolex.utilitaires import verif_taille

def telecharger_legifrance(url, fichier, cache_html, force=False):
    
    if os.path.exists(os.path.join(cache_html, fichier)):
        touch = datetime.fromtimestamp(os.stat(os.path.join(cache_html, fichier)).st_mtime)
        delta = datetime.today() - touch
        
        if not force or not isinstance(force, bool) and isinstance(force, (int, long, float)) and delta.total_seconds() < force:
            print('* Téléchargement de ' + url + ' (cache)')
            return True
    
    print('* Téléchargement de ' + url)
    return telecharger('http://legifrance.gouv.fr/' + url, os.path.join(cache_html, fichier))


# Le tuple renvoyé correspond à (Nom, cidTexte, estUnCode, 'xml'|'xml-html'|'html'|None)
def obtenir_identifiants(cles, cache):
    
    codes, sedoc = telecharger_index_codes(cache)
    
    ncles = [''] * len(cles)
    for i in range(0, len(cles)):
        
        cle = re.sub('’', '\'', re.sub('[_-]', ' ', cles[i]))
        cle = cle[0].upper() + cle[1:].lower()
        
        if cle == 'Constitution de 1958' or cle.upper() == 'LEGITEXT000006071194':
            ncles[i] = ('Constitution de 1958', 'LEGITEXT000006071194', False, None)
        elif cle in sedoc.keys():
            ncles[i] = (re.sub('\'', '’', cle), sedoc[cle], True, None)
        elif cle.upper() in codes.keys():
            ncles[i] = (codes[cle.upper()], cle.upper(), True, None)
        else:
            ncles[i] = (None, cles[i], None, None)
    
    return ncles


def telecharger_index_codes(cache):
    
    codes = {}
    sedoc = {}
    
    # Télécharger le cas échéant le formulaire de recherche contenant le nom des codes
    path(os.path.join(cache, 'html')).mkdir_p()
    telecharger_legifrance('initRechCodeArticle.do', 'recherche.html', os.path.join(cache, 'html'), 86400)
    fichier_recherche = open(os.path.join(cache, 'html', 'recherche.html'), 'r')
    soup = BeautifulSoup(fichier_recherche.read())
    
    # Récupérer les informations
    codes_html = soup.select('select[name="cidTexte"]')[0].findAll('option')
    for code_html in codes_html:
        if code_html.has_attr('title') and code_html.has_attr('value'):
            codes[code_html.attrs['value']] = code_html.attrs['title']
            sedoc[code_html.attrs['title']] = code_html.attrs['value']
    
    return codes, sedoc


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
    return type_fichier, recent, telecharger_cache(url, os.path.join(cache, 'tar', identifiant + '-' + type_fichier + '-' + recent + '.tar.gz'))

