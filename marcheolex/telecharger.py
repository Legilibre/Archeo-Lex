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
import shutil

import ftplib
import subprocess
from datetime import datetime
from path import path
from bs4 import BeautifulSoup
import peewee

from marcheolex import NonImplementeException, \
                       NomBaseException, FondationNonUniqueException, \
                       FondationNonTrouveeException
from marcheolex import bases, serveurs, fichiers_fond, fichiers_majo
from marcheolex.basededonnees import Livraison  
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
    soup = BeautifulSoup(fichier_recherche.read(), 'xml')
    
    # Récupérer les informations
    codes_html = soup.select('select[name="cidTexte"]')[0].findAll('option')
    for code_html in codes_html:
        if code_html.has_attr('title') and code_html.has_attr('value'):
            codes[code_html.attrs['value']] = code_html.attrs['title']
            sedoc[code_html.attrs['title']] = code_html.attrs['value']
    
    return codes, sedoc

# Télécharger une base spécifiée à une livraison spécifiée
# 
# @param str base 'JORF', 'LEGI', 'KALI', 'CNIL', 'CONSTIT', 'CIRCULAIRES'
# @param str|datetime livraison 'tout' pour télécharger toute la base
#                               'fondation' pour télécharger la fondation
#                               objet datetime pour tout jusqu’à la date
#                               'AAAAMMJJ-HHMMJJ' idem datetime
# @param str cache
def telecharger_fichiers_base(base, livraison='fondation', cache='cache'):
    
    # Vérification des paramètres
    base = base.upper()
    if base not in bases:
        raise NomBaseException()
    if livraison not in ['fondation','tout'] and \
       not isinstance(livraison, datetime):
        livraison = datetime.strptime(livraison, '%Y%m%d-%H%M%S')
    
    # Télécharger les fichiers
    date_fond, dates_majo = telecharger_base(base, livraison, cache)
    
    # Télécharger les fichiers
    decompresser_base(base, date_fond, dates_majo, cache)


# Téléchargement des bases juridiques
# 
# @param str base 'JORF', 'LEGI', 'KALI', 'CNIL', 'CONSTIT', 'CIRCULAIRES'
# @param str|datetime livraison 'tout' pour télécharger toute la base
#                               'fondation' pour télécharger la fondation
#                               objet datetime pour tout jusqu’à la date
#                               'AAAAMMJJ-HHMMJJ' idem datetime
# @param str cache
def telecharger_base(base, livraison='tout', cache='cache'):
    
    # Vérification des paramètres
    base = base.upper()
    if base not in bases:
        raise NomBaseException()
    if livraison not in ['fondation','tout'] and \
       not isinstance(livraison, datetime):
        livraison = datetime.strptime(livraison, '%Y%m%d-%H%M%S')
    if serveurs[base][0] != 'ftp':
        raise NonImplementeException()
    
    # Créer le dossier de cache des fichiers téléchargés
    path(os.path.join(cache, 'tar')).mkdir_p()
    
    # Connexion FTP
    serveur = serveurs[base][0] + ':' + \
              '//' + serveurs[base][2] + ':' + serveurs[base][3] + \
              '@' + serveurs[base][1] + serveurs[base][4]
    
    connexion_ftp = ftplib.FTP(serveurs[base][1], \
                               serveurs[base][2], \
                               serveurs[base][3])
    
    # Reconnaître les dates des fichiers
    connexion_ftp.cwd(serveurs[base][4])
    fichiers = connexion_ftp.nlst()
    date_fond = None
    dates_majo = []
    
    for fichier in fichiers:
        
        # Si c’est un fichier de dump complet
        try:
            datetime.strptime(fichier, fichiers_fond[base])
            if date_fond: raise FondationNonUniqueException()
            date_fond = datetime.strptime(fichier, fichiers_fond[base])
        except ValueError:
            pass
        
        # Si c’est un fichier de dump incrémental
        try:
            dates_majo.append(datetime.strptime(fichier, fichiers_majo[base]))
        except ValueError:
            pass
    
    # Normaliser les paramètres relatifs aux dates
    dates_majo.sort()
    if not date_fond:
        raise FondationNonTrouveeException()
    if livraison == 'fondation':
        livraison = date_fond
    if livraison == 'tout':
        livraison = dates_majo[-1]
    dates_majo = [date for date in dates_majo if date <= livraison]
    
    # Téléchargement du dump complet
    telecharger_cache(serveur + date_fond.strftime(fichiers_fond[base]),
                      os.path.join(cache, 'tar', base + 
                      date_fond.strftime('-fond-%Y%m%d-%H%M%S.tar.gz')))
    
    # Téléchargement des dumps incrémentaux
    for date_majo in dates_majo:
        
        telecharger_cache(serveur + date_majo.strftime(fichiers_majo[base]),
                          os.path.join(cache, 'tar', base + 
                          date_majo.strftime('-majo-%Y%m%d-%H%M%S.tar.gz')))
    
    # Clôturer la connexion
    connexion_ftp.close()
    
    return date_fond, dates_majo


# Décompresser les fichiers téléchargés
# 
# @param str base 'JORF', 'LEGI', 'KALI', 'CNIL', 'CONSTIT', 'CIRCULAIRES'
# @param datetime date_fond date du dump complet
# @param list[datetime] date_majo dates des dumps incrémentaux
# @param str cache
def decompresser_base(base, date_fond, dates_majo, cache='cache'):
    
    # Vérification des paramètres
    base = base.upper()
    if base not in bases:
        raise NomBaseException()
    if not isinstance(date_fond, datetime) or not isinstance(dates_majo, list):
        raise ValueError()
    for date in dates_majo:
        if not isinstance(date, datetime):
            raise ValueError()
    
    # Créer le répertoire rattaché à ce dump complet
    rep = os.path.join(cache, 'bases-xml', date_fond.strftime('%Y%m%d-%H%M%S'))
    path(rep).mkdir_p()
    
    # Décompresser le dump complet
    date = date_fond.strftime('%Y%m%d-%H%M%S')
    if not os.path.exists(os.path.join(rep, 'fond-' + date)) or \
       os.path.exists(os.path.join(rep, 'fond-' + date, 'erreur-tar')):
        
        if os.path.exists(os.path.join(rep, 'fond-' + date, 'erreur-tar')):
            shutil.rmtree(os.path.join(rep, 'fond-' + date))
        path(os.path.join(rep, 'fond-' + date)).mkdir_p()
        open(os.path.join(rep, 'fond-' + date, 'erreur-tar'), 'w').close()
        subprocess.call(['tar', 'xzf',
            os.path.join(cache, 'tar', base + '-fond-' + date + '.tar.gz'),
            '-C', os.path.join(rep, 'fond-' + date)])
        os.remove(os.path.join(rep, 'fond-' + date, 'erreur-tar'))
        
    
    # Inscrire cette livraison dans la base de données
    try:
        entree_livraison = Livraison.get(Livraison.date == date_fond)
    except Livraison.DoesNotExist:
        entree_livraison = Livraison.create(
                date=date_fond,
                type='fondation',
                base=base,
                precedent=None,
                fondation=None
            )
    entree_livraison_fondation = entree_livraison
    
    # Décompresser les dumps incrémentaux
    for date_majo in dates_majo:
        
        date = date_majo.strftime('%Y%m%d-%H%M%S')
        if not os.path.exists(os.path.join(rep, 'majo-' + date)) or \
           os.path.exists(os.path.join(rep, date)) or \
           os.path.exists(os.path.join(rep, 'majo-' + date, 'erreur-tar')):
            
            if os.path.exists(os.path.join(rep, date)):
                shutil.rmtree(os.path.join(rep, date), True)
                shutil.rmtree(os.path.join(rep, 'majo-' + date), True)
            if os.path.exists(os.path.join(rep, 'majo-' + date, 'erreur-tar')):
                shutil.rmtree(os.path.join(rep, 'majo-' + date), True)
            path(os.path.join(rep, date)).mkdir_p()
            open(os.path.join(rep, date, 'erreur-tar'), 'w').close()
            subprocess.call(['tar', 'xzf',
                os.path.join(cache, 'tar', base + '-majo-' + date + '.tar.gz'),
                '-C', rep])
            os.rename(os.path.join(rep, date),
                      os.path.join(rep, 'majo-' + date))
            os.remove(os.path.join(rep, 'majo-' + date, 'erreur-tar'))
        
        # Inscrire cette livraison dans la base de données
        try:
            entree_livraison = Livraison.get(Livraison.date == date_majo)
        except Livraison.DoesNotExist:
            entree_livraison = Livraison.create(
                    date=date_majo,
                    type='miseajour',
                    base=base,
                    precedent=entree_livraison,
                    fondation=entree_livraison_fondation
                )

