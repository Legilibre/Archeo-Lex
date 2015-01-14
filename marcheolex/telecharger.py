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
import subprocess
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


def telecharger_fichiers_base(identifiant, date_maj, cache):
    
    identifiant = identifiant.upper()
    type, dates = telecharger_base(identifiant, 'fondation', cache)
    date_fondation = dates[0]
    
    # Télécharger les mises à jour
    dates_miseajour = []
    if date_maj != 'fondation' and date_fondation != date_maj:
        if date_maj == 'dernière':
            date_maj = '29990101'
        type, dates_miseajour = telecharger_base(identifiant, date_maj, cache)
    
    # Décompresser les fichiers
    if not os.path.exists(os.path.join(cache, 'bases-xml', date_fondation, 'fond-'+date_fondation)):
        path(os.path.join(cache, 'bases-xml', date_fondation)).mkdir_p()
        path(os.path.join(cache, 'bases-xml', date_fondation, 'fond-'+date_fondation)).mkdir_p()
        subprocess.call(['tar', 'xzf', os.path.join(cache, 'tar', identifiant + '-fond-' + date_fondation + '.tar.gz'), '-C', os.path.join(cache, 'bases-xml', date_fondation, 'fond-'+date_fondation)])
        
        # Inscrire cette livraison dans la base de données
        entree_livraison = Livraison.create(
                date=normalise_datetime(date_fondation),
                type='fondation',
                base=identifiant,
                precedent=None,
                fondation=None
            )
        entree_livraison_fondation = entree_livraison
    
    if type == 'majo':
        for date in range(0,len(dates_miseajour)):
            if not os.path.exists(os.path.join(cache, 'bases-xml', date_fondation, 'majo-'+dates_miseajour[date])):
                path(os.path.join(cache, 'bases-xml', date_fondation, 'majo-'+dates_miseajour[date])).mkdir_p()
                subprocess.call(['tar', 'xzf', '-C', os.path.join(cache, 'bases-xml', date_fondation, 'majo-'+dates_miseajour[date]), os.path.join(cache, 'tar', identifiant + '-majo-' + dates_miseajour[date] + '.tar.gz')])
                
                # Inscrire cette livraison dans la base de données
                entree_livraison = Livraison.create(
                        date=normalise_datetime(dates_miseajour[date]),
                        type='miseajour',
                        base=identifiant,
                        precedent=entree_livraison,
                        fondation=entree_livraison_fondation
                    )



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
    elif not isinstance(date_maj, str) and not date_maj == None and date_maj != 'fondation':
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
        'JORF': 'Freemium_jorf_global_%Y%m%d-%H%M%S.tar.gz',
        'LEGI': 'Freemium_legi_global_%Y%m%d-%H%M%S.tar.gz',
        'KALI': 'Freemium_kali__%Y%m%d-%H%M%S.tar.gz',
        'CNIL': 'Freemium_cnil_global_%Y%m%d-%H%M%S.tar.gz',
        'CONSTIT': 'Freemium_constit_global_%Y%m%d-%H%M%S.tar.gz',
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
    if date_maj == None or date_maj == 'fondation':
        prefixe = string.split(fichier_base[identifiant], '%')[0]
        type_fichier = 'fond'
    else:
        prefixe = string.split(fichier_majo[identifiant], '%')[0]
        type_fichier = 'majo'
    dates = []
    for fichier in liste_fichiers:
        if fichier.startswith(prefixe):
            dates.append(re.sub(prefixe + '([0-9-]+)\.tar\.gz', r'\1', fichier))
    dates.sort(None, None, True)
    date_selectionnee = 0
    dates_selectionnees = []
    if date_maj and date_maj != 'fondation':
        if len(date_maj) == 8:
            date_maj = date_maj + '-235959'
        if re.match('^(0|-\d+)$', date_maj):
            date_selectionnee = -int(date_maj)
        else:
            while date_selectionnee < len(dates) and dates[date_selectionnee] > date_maj:
                dates_selectionnees[date_selectionnee] = dates[date_selectionnee]
                date_selectionnee = date_selectionnee + 1
            if date_selectionnee == len(dates):
                raise Exception()
    else:
        dates_selectionnees.append(dates[0])
    recent = dates[date_selectionnee]
    
    # Téléchargement des fichiers
    for date_selectionnee in range(0,len(dates_selectionnees)):
        
        # Création de l’URL
        url = serveur[identifiant][0] + '://' + serveur[identifiant][2] + ':' + serveur[identifiant][3] + '@' + serveur[identifiant][1] + '/' + prefixe + dates_selectionnees[date_selectionnee] + '.tar.gz'
        
        # Vérification de la taille disponible
        if not verif_taille(connexion_ftp.size(prefixe + recent + '.tar.gz'), cache) and not os.path.exists(identifiant + '-' + type_fichier + '-' + dates_selectionnees[date_selectionnee] + '.tar.gz'):
            raise Exception()
        
        # Téléchargement de la base demandée
        telecharger_cache(url, os.path.join(cache, 'tar', identifiant + '-' + type_fichier + '-' + dates_selectionnees[date_selectionnee] + '.tar.gz'))
    
    connexion_ftp.close()
    
    return type_fichier, dates_selectionnees

# Dépacketer la base
def ouvrir_base(identifiant, date_maj, cache):
    
    identifiant = identifiant.upper()
    if identifiant not in ['JORF', 'LEGI', 'KALI', 'CNIL', 'CONSTIT']:
        raise Exception()
    if isinstance(date_maj, int):
        date_maj = str(date_maj)
    elif not isinstance(date_maj, str) and not date_maj == None:
        raise Exception()
    if date_maj == None:
        type_fichier = 'fond'
    else:
        type_fichier = 'majo'
    
    subprocess.call(['tar', 'xzf', os.path.join(cache, 'tar', identifiant + '-' + type_fichier + '-' + date_maj + '.tar.gz')])
    
