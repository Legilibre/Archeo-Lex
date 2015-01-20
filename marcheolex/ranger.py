# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module lit les métadonnées et les insère dans la base de données
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
import sys
from bs4 import BeautifulSoup
from datetime import datetime

from marcheolex import FichierNonExistantException
from marcheolex.basededonnees import Livraison
from marcheolex.basededonnees import Texte
from marcheolex.basededonnees import Version_texte
from marcheolex.basededonnees import Version_section
from marcheolex.basededonnees import Version_article
from marcheolex.basededonnees import Livraison_texte
from marcheolex.basededonnees import Liste_sections
from marcheolex.basededonnees import Liste_articles
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import normalise_date
from marcheolex.utilitaires import comp_infini


# Ranger un ensemble de textes d’une base XML
def ranger(base, textes, livraison, cache):
    
    for texte in textes:
        
        lire_code_xml(base, texte, livraison, cache)


# Lire un texte dans une base XML
def lire_code_xml(base, cle, livraison, cache):
    
    if not cle[2]:
        return
    if livraison not in ['fondation','tout'] and \
       not isinstance(livraison, datetime):
        livraison = datetime.strptime(livraison, '%Y%m%d-%H%M%S')
    
    # TODO !! test
    entree_livraison = Livraison.create(
                date=datetime(2015, 1, 7, 14, 45, 52),
                type='fondation',
                base='LEGI',
                precedent=None,
                fondation=None
            )
    
    # Obtenir la livraison
    cidTexte = cle[1]
    if livraison == 'fondation':
        entree_livraison = Livraison.select(). \
            where(Livraison.type == 'fondation'). \
            order_by(Livraison.date.desc()).limit(1)
    elif livraison == 'tout':
        entree_livraison = Livraison.select(). \
            order_by(Livraison.date.desc()).limit(1)
    else:
        entree_livraison = Livraison.get(Livraison.date == livraison)
    
    # Construire le chemin de base
    if entree_livraison.type == 'fondation':
        date_fond = entree_livraison.date.strftime('%Y%m%d-%H%M%S')
    else:
        date_fond = entree_livraison.fondation.strftime('%Y%m%d-%H%M%S')
    chemin_base = os.path.join(cache, 'bases-xml')
    chemin_fond = os.path.join(chemin_base, date_fond)
    
    # Parcourir les livraisons en sens croissant
    while entree_livraison:
        
        # Chemin de la livraison
        date_majo = entree_livraison.date.strftime('%Y%m%d-%H%M%S')
        if entree_livraison.type == 'fondation':
            chemin_majo = os.path.join(chemin_fond, 'fond-' + date_majo)
        else:
            chemin_majo = os.path.join(chemin_fond, 'majo-' + date_majo)
        
        # Chemin du texte
        chemin = os.path.join(chemin_majo, chemin_texte(cidTexte))
        if not os.path.exists(chemin):
            raise Exception()
        
        # Lire les informations sur le texte
        ranger_texte_xml(entree_livraison, base, chemin, cidTexte, 'code')
        
        # Ouvrir la livraison suivante
        entree_livraison = Livraison.get(Livraison.suivante == entree_livraison)


# Vérifier si le texte existe, et en fonction de cela ajouter ou mettre à jour
def ranger_texte_xml(livraison, base, chemin_base, cidTexte, nature_attendue=None):
    
    # Lecture du fichier XML texte/version/[cid].xml
    version = lire_base_version(chemin_base, cidTexte)
    
    # Lecture brute du fichier XML texte/struct
    struct = lire_base_struct(chemin_base, cidTexte)
    
    # Vérifications
    if not cidTexte == version['CID']:
        raise Exception()
    if nature_attendue and not version['NATURE'] == nature_attendue.upper() or not struct['NATURE'] == nature_attendue.upper():
        raise Exception()
    if not version['DATE_TEXTE'] == struct['DATE_TEXTE']:
        raise Exception()
    if not version['DATE_PUBLI'] == struct['DATE_PUBLI']:
        raise Exception()
    if not len(struct['VERSION']) == 1:  # texte/version ne peut avoir qu’une seule version, donc texte/struct également et elles doivent correspondre
        raise Exception()
    
    # Inscription du texte
    try:
        entree_texte = Texte.get(Texte.cid == version['CID'])
    except:
        entree_texte = Texte.create(
            cid=version['CID'].upper(),
            nor=version['NOR'].upper(),
            base=base,
            livraison=None
        )
    '''
    # Enregistrement de la Version_texte d’autorité
    # TODO gérer les mises à jour
    
    try:
        entree_version_texte = Version_texte.get(Version_texte.texte == entree_texte)
    except:
        entree_version_texte = Version_texte.create(
            titre=version['TITRE'],
            titre_long=version['TITREFULL'],
            nature=version['NATURE'].lower(),
            date_texte=version['DATE_TEXTE'],
            date_publi=version['DATE_PUBLI'],
            date_modif=version['DERNIERE_MODIFICATION'],
            etat_juridique=version['ETAT'].lower(),
            vigueur_debut=version['DATE_DEBUT'],
            vigueur_fin=version['DATE_FIN'],
            version_prec=None,
            texte=entree_texte
        )
    '''
    # Initialisation du suivi des dates de changement
    dates = set([version['DATE_DEBUT'], version['DATE_FIN']])
    sections = set()
    articles = set()
    rows_sections = set()
    rows_articles = set()
    
    # Ajouter récursivement les sections et articles
    dates, sections, articles, rows_sections, rows_articles = ranger_sections_xml(chemin_base, struct['LIEN_SECTION_TA'], struct['LIEN_ART'], entree_texte, None, dates, sections, articles, cidTexte, 1, rows_sections, rows_articles)
    print('')
    print(len(dates))
    print(len(sections))
    print(len(articles))
    print(len(rows_sections))
    print(len(rows_articles))
    
    # Enregistrer les versions de texte
    enregistrer_versions_texte(dates, sections, articles, entree_texte, rows_sections, rows_articles)


def enregistrer_versions_texte(dates, sections, articles, entree_texte, rows_sections, rows_articles):
    
    # Chercher les versions de textes de cette livraison
    dates = list(dates)
    dates.sort(cmp=comp_infini)

    def obtenir_sections(sections):
        for section in sections:
            yield {'id': section[0],
                   'nom': section[1],
                   'etat_juridique': section[2],
                   'niveau': section[3],
                   'numero': section[4],
                   'vigueur_debut': section[5],
                   'vigueur_fin': section[6],
                   'texte': section[7]}
    
    def obtenir_articles(articles):
        for article in articles:
            yield {'id': article[0],
                   'nom': article[1],
                   'etat_juridique': article[2],
                   'numero': article[3],
                   'vigueur_debut': article[4],
                   'vigueur_fin': article[5],
                   'condensat': article[6],
                   'texte': article[7]}
    
    # Import des enregistrements sections et articles
    # Il ne semble pas possible d’ajouter plus de 500 enregistrements
    #  par appel à insert_many, dont acte
    slice = 500
    rows_sections = list(rows_sections)
    rows_articles = list(rows_articles)
    for i in range(0,int(len(rows_sections)/slice+1)):
        Version_section.insert_many(obtenir_sections(rows_sections[i*slice:(i+1)*slice])).execute()
    for i in range(0,int(len(rows_articles)/slice+1)):
        Version_article.insert_many(obtenir_articles(rows_articles[i*slice:(i+1)*slice])).execute()
    #Version_section.insert_many(obtenir_sections(rows_sections)).execute()
    #Version_article.insert_many(obtenir_articles(rows_articles)).execute()
    
    
    if entree_texte.livraison:
        entree_version_texte = Livraison_texte.select().where(
            Livraison_texte.livraison == entree_texte.livraison &
            Livraison_texte.texte == entree_texte
        ).order_by(Livraison_texte.version_texte.desc()).limit(1)
        
        while entree_version_texte.version_texte.date != dates[0]:
            entree_version_texte = Version_texte.select().where(
                Version_texte.precedent == entree_version_texte
            )
            
    
    for i in range(len(dates) - 1):
        
        # Enregistrement de cette version de texte, sauf si elle existe
        try:
            entree_version_texte = Version_texte.select().where(
                Version_texte.titre == version['TITRE'] &
                Version_texte.titre_long == version['TITREFULL'] &
                Version_texte.nature == version['NATURE'].lower() &
                Version_texte.date_texte == version['DATE_TEXTE'] &
                Version_texte.date_publi == version['DATE_PUBLI'] &
                Version_texte.date_modif == version['DERNIERE_MODIFICATION'] &
                Version_texte.etat_juridique == version['ETAT'].lower() &
                Version_texte.vigueur_debut == dates[i] &
                Version_texte.vigueur_fin == dates[i+1] &
                Version_texte.texte == entree_texte #&
                #Version_texte.version_prec == entree_version_texte
            )
        except Version_texte.DoesNotExist:
            entree_version_texte = Version_texte.create(
                titre = version['TITRE'],
                titre_long = version['TITREFULL'],
                nature=version['NATURE'].lower(),
                date_texte=version['DATE_TEXTE'],
                date_publi=version['DATE_PUBLI'],
                date_modif=version['DERNIERE_MODIFICATION'],
                etat_juridique = version['ETAT'].lower(),
                vigueur_debut = dates[i],
                vigueur_fin = dates[i+1],
                texte = entree_texte,
                #version_prec=entree_version_texte
            )
        
        # Inscription du lien entre texte, livraison et version de texte
        Livraison_texte.create(
            livraison = livraison,
            version_texte = entree_version_texte,
            texte = entree_texte
        )
        
        # Inscription du lien entre livraison et section
        Liste_sections.create(
            version_section = entree_version_section,
            version_texte = entree_version_texte
        )
        
        # Lister les sections
        #Liste_
    
    # Enregistrer cette livraison du texte comme étant calculée
    entree_texte.livraison = livraison
    entree_texte.save()


# Parcourir récursivement les sections
# - enregistrer celles du niveau N (N≥1)
# - ouvrir les fichiers correspondant à ces sections
# - appeler ranger_sections_xml sur les nœuds de STRUCTURE_TA
def ranger_sections_xml(chemin_base, coll_sections, coll_articles, entree_texte, version_section_parente, dates, sections, articles, cidTexte, niv, rows_sections, rows_articles):
    
    # Prévenir les récursions infinies - les specs indiquent un max de 10
    if niv == 11:
        raise Exception()
    
    # Traiter les articles à ce niveau
    #dates_texte, ensemble_articles = ranger_articles_xml(chemin_base, coll_articles, version_section_parente, entree_texte, dates_texte, ensemble_articles)
    dates, articles, rows_articles = ranger_articles_xml(chemin_base, coll_articles, entree_texte, dates, articles, rows_articles)
    
    for i, section in enumerate(coll_sections):
        
        # Affichage de l’avancement
        compteur_recursif(i+1, len(coll_sections), False)
        
        cid = section['cid']
        id = section['id']
        nom = section.text
        etat_juridique = section['etat']
        niveau = section['niv']
        vigueur_debut = normalise_date(section['debut'])
        vigueur_fin = normalise_date(section['fin'])
        url = section['url'][1:]
        numero = i+1
        
        # Prise en compte de cette version de section
        try:
            entree_version_section = Version_section.select().where(
                (Version_section.id == id) &
                #(Version_section.id_parent == version_section_parente) &
                (Version_section.nom == nom) &
                (Version_section.etat_juridique == etat_juridique) &
                (Version_section.niveau == niveau) &
                (Version_section.numero == numero) &
                (Version_section.vigueur_debut == vigueur_debut) &
                (Version_section.vigueur_fin == vigueur_fin) &
                (Version_section.texte == entree_texte)
            ).get()
            sections |= {entree_version_section.id}
        except Version_section.DoesNotExist:
            rows_sections |= {(id, nom, etat_juridique, niveau, numero, vigueur_debut, vigueur_fin, entree_texte.cid)}
        
        # Prise en compte des dates de vigueur
        dates |= {vigueur_debut, vigueur_fin}
        
        # Continuer récursivement
        section_ta = lire_base_section_ta(chemin_base, url)
        
        dates, sections, articles, rows_sections, rows_articles = ranger_sections_xml(chemin_base, section_ta['LIEN_SECTION_TA'], section_ta['LIEN_ART'], entree_texte, None, dates, sections, articles, cidTexte, niv+1, rows_sections, rows_articles)
        
        # Affichage de l’avancement
        compteur_recursif()
    
    return dates, sections, articles, rows_sections, rows_articles


def ranger_articles_xml(chemin_base, coll_articles, entree_texte, dates, articles, rows_articles):
    
    # Si pas d’article dans cette section
    if coll_articles == None:
        return dates_texte, ensemble_articles, rows_articles
    
    # Sinon itérer sur les articles
    for i, article in enumerate(coll_articles):
        
        # Affichage de l’avancement
        compteur_recursif(i+1, len(coll_articles), True)
        
        # Lecture brute des attributs XML
        id = article['id']
        nom = article['num']
        etat_juridique = article['etat']
        vigueur_debut = normalise_date(article['debut'])
        vigueur_fin = normalise_date(article['fin'])
        numero = i+1
        
        # Prise en compte de cette version d’article        
        try:
            entree_article = Version_article.select().where(
                (Version_article.id == id) &
                #(Version_article.version_section == entree_version_section) &
                (Version_article.nom == nom) &
                (Version_article.etat_juridique == etat_juridique) &
                (Version_article.numero == numero) &
                (Version_article.vigueur_debut == vigueur_debut) &
                (Version_article.vigueur_fin == vigueur_fin) &
                (Version_article.condensat == None) &
                (Version_article.texte == entree_texte)
            ).get()
            articles |= {entree_article.id}
        except Version_article.DoesNotExist:
            rows_articles |= {(id,  nom, etat_juridique, numero, vigueur_debut, vigueur_fin, None, entree_texte.cid)}
        
        # Prise en compte des dates de vigueur
        dates |= {vigueur_debut, vigueur_fin}
        
        # Affichage de l’avancement
        compteur_recursif()
    
    return dates, articles, rows_articles


# Lire les propriétés du fichier texte/version/[cid].xml
def lire_base_version(chemin_base, cid):
    
    # Initialiser le dictionnaire résultat
    version = dict()
    
    # Ouvrir le fichier XML
    chemin_xml = os.path.join(chemin_base, 'texte', 'version', cid + '.xml')
    if not os.path.exists(chemin_xml):
        raise FichierNonExistantException()
    f_version = open(chemin_xml, 'r')
    soup = BeautifulSoup(f_version.read(), 'xml')
    f_version.close()
    
    # Lecture des éléments englobants
    META = soup.find('META')
    META_COMMUN = META.find('META_COMMUN')
    META_SPEC = META.find('META_SPEC')
    META_TEXTE_CHRONICLE = META_SPEC.find('META_TEXTE_CHRONICLE')
    META_TEXTE_VERSION = META_SPEC.find('META_TEXTE_VERSION')
    
    # Lecture des éléments feuille
    version['NATURE'] = META_COMMUN.find('NATURE').text
    version['CID'] = META_TEXTE_CHRONICLE.find('CID').text
    version['NOR'] = META_TEXTE_CHRONICLE.find('NOR').text
    version['DATE_TEXTE'] = META_TEXTE_CHRONICLE.find('DATE_TEXTE').text
    version['DATE_PUBLI'] = META_TEXTE_CHRONICLE.find('DATE_PUBLI').text
    version['DERNIERE_MODIFICATION'] = \
        META_TEXTE_CHRONICLE.find('DERNIERE_MODIFICATION').text
    version['TITRE'] = META_TEXTE_VERSION.find('TITRE').text
    version['TITREFULL'] = META_TEXTE_VERSION.find('TITREFULL').text
    version['DATE_DEBUT'] = META_TEXTE_VERSION.find('DATE_DEBUT').text
    version['DATE_FIN'] = META_TEXTE_VERSION.find('DATE_FIN').text
    version['ETAT'] = META_TEXTE_VERSION.find('ETAT').text
    
    # Normalisations
    version['DATE_TEXTE'] = normalise_date(version['DATE_TEXTE'])
    version['DATE_PUBLI'] = normalise_date(version['DATE_PUBLI'])
    version['DATE_DEBUT'] = normalise_date(version['DATE_DEBUT'])
    version['DATE_FIN'] = normalise_date(version['DATE_FIN'])
    
    return version


# Lire les propriétés du fichier texte/struct/[cid].xml
def lire_base_struct(chemin_base, cid):
    
    # Initialiser le dictionnaire résultat
    struct = dict()
    
    # Ouvrir le fichier XML
    chemin_xml = os.path.join(chemin_base, 'texte', 'struct', cid + '.xml')
    if not os.path.exists(chemin_xml):
        raise Exception()
    f_struct = open(chemin_xml, 'r')
    soup = BeautifulSoup(f_struct.read(), 'xml')
    f_struct.close()
    
    # Lecture des éléments englobants
    META = soup.find('META')
    META_COMMUN = META.find('META_COMMUN')
    META_SPEC = META.find('META_SPEC')
    META_TEXTE_CHRONICLE = META_SPEC.find('META_TEXTE_CHRONICLE')
    META_TEXTE_VERSION = META_SPEC.find('META_TEXTE_VERSION')
    VERSIONS = soup.find('VERSIONS')
    STRUCT = soup.find('STRUCT')

    # Lecture des éléments feuille
    struct['NATURE'] = META_COMMUN.find('NATURE').text
    struct['CID'] = META_TEXTE_CHRONICLE.find('CID').text
    struct['NOR'] = META_TEXTE_CHRONICLE.find('NOR').text
    struct['DATE_TEXTE'] = META_TEXTE_CHRONICLE.find('DATE_TEXTE').text
    struct['DATE_PUBLI'] = META_TEXTE_CHRONICLE.find('DATE_PUBLI').text
    struct['VERSION'] = VERSIONS.find_all('VERSION')
    struct['VERSION_etat'] = struct['VERSION'][0]['etat']
    struct['LIEN_TXT'] = struct['VERSION'][0].find('LIEN_TXT')
    struct['LIEN_TXT_id'] = struct['LIEN_TXT']['id']
    struct['LIEN_TXT_debut'] = struct['LIEN_TXT']['debut']
    struct['LIEN_TXT_fin'] = struct['LIEN_TXT']['fin']
    struct['LIEN_ART'] = STRUCT.find_all('LIEN_ART')
    struct['LIEN_SECTION_TA'] = STRUCT.find_all('LIEN_SECTION_TA')
    
    # Normalisations
    struct['DATE_TEXTE'] = normalise_date(struct['DATE_TEXTE'])
    struct['DATE_PUBLI'] = normalise_date(struct['DATE_PUBLI'])
    
    return struct


# Lire les propriétés du fichier section_ta/[chemin_id]
def lire_base_section_ta(chemin_base, chemin_id):
    
    # Initialiser le dictionnaire résultat
    section_ta = dict()
    
    # Ouvrir le fichier XML
    chemin_xml = os.path.join(chemin_base, 'section_ta', chemin_id)
    f_section_ta = open(chemin_xml, 'r')
    soup = BeautifulSoup(f_section_ta.read(), 'xml')
    f_section_ta.close()
    
    # Lecture des éléments englobants
    STRUCTURE_TA = soup.find('STRUCTURE_TA')
    
    # Lecture des éléments feuille
    section_ta['LIEN_SECTION_TA'] = STRUCTURE_TA.find_all('LIEN_SECTION_TA')
    section_ta['LIEN_ART'] = STRUCTURE_TA.find_all('LIEN_ART')
    
    return section_ta


# Compteur récursif
def compteur_recursif(index = None, total = None, feuille = False):
    
    if not hasattr(compteur_recursif, 'avancement') or total == 0:
        compteur_recursif.avancement = []
    
    # Initialisation de l’index
    if index >= 1:
        
        if index == 1:
            compteur_recursif.avancement += [(index, total, feuille)]
        else:
            compteur_recursif.avancement[-1] = (index, total, feuille)
        
        if feuille:
            print('({}/{})'.format(index, total), end='')
        else:
            print('{}/{} → '.format(index, total), end='')
    
    # Effacement de l’index avant de passer au suivant
    elif index == None:
        
        index = compteur_recursif.avancement[-1][0]
        total = compteur_recursif.avancement[-1][1]
        feuille = compteur_recursif.avancement[-1][2]
        
        if index == total:
            compteur_recursif.avancement.pop()
        
        if feuille:
            taille = len('({}/{})'.format(index, total))
        else:
            taille = len('{}/{}'.format(index, total))+3
        
        print('\033[' + str(taille) + 'D' + (''.join([' ' * taille])) + \
              '\033[' + str(taille) + 'D', end='')
    
    sys.stdout.flush()

