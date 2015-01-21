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
import math

from bs4 import BeautifulSoup
from datetime import datetime

from marcheolex import FichierNonExistantException
from marcheolex import tranches_bdd
from marcheolex.basededonnees import Livraison
from marcheolex.basededonnees import Texte
from marcheolex.basededonnees import Version_texte
from marcheolex.basededonnees import Version_section
from marcheolex.basededonnees import Version_article
from marcheolex.basededonnees import Livraison_texte
from marcheolex.basededonnees import Liste_sections
from marcheolex.basededonnees import Liste_articles
from marcheolex.basededonnees import Travaux_articles
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import decompose_cid
from marcheolex.utilitaires import normalise_date
from marcheolex.utilitaires import comp_infini
from marcheolex.utilitaires import comp_infini_strict


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
        try:
            entree_livraison = Livraison.get(Livraison.suivante == entree_livraison)
        except Livraison.DoesNotExist:
            entree_livraison = None


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
    
    # Initialisation du suivi des dates de changement
    dates = set([version['DATE_DEBUT'], version['DATE_FIN']])
    autres_sections = set()
    autres_articles = set()
    nouvelles_sections = set()
    nouveaux_articles = set()
    
    # Ajouter récursivement les sections et articles
    dates, autres_sections, autres_articles, nouvelles_sections, nouveaux_articles = ranger_sections_xml(chemin_base, struct['LIEN_SECTION_TA'], struct['LIEN_ART'], entree_texte, None, dates, autres_sections, autres_articles, 1, nouvelles_sections, nouveaux_articles)
    print('')
    print(len(dates))
    print(len(autres_sections))
    print(len(autres_articles))
    print(len(nouvelles_sections))
    print(len(nouveaux_articles))
    
    # Enregistrer les versions de texte
    enregistrer_versions_texte(version, livraison, dates, autres_sections, autres_articles, entree_texte, nouvelles_sections, nouveaux_articles, chemin_base)


# Parcourir récursivement les sections
# - enregistrer celles du niveau N (N≥1)
# - ouvrir les fichiers correspondant à ces sections
# - appeler ranger_sections_xml sur les nœuds de STRUCTURE_TA
def ranger_sections_xml(chemin_base, coll_sections, coll_articles, \
                        entree_texte, version_section_parente, dates, \
                        autres_sections, autres_articles, niv, \
                        nouvelles_sections, nouveaux_articles):
    
    # Prévenir les récursions infinies - les specs indiquent un max de 10
    if niv == 11:
        raise Exception()
    
    # Traiter les articles à ce niveau
    dates, autres_articles, nouveaux_articles = ranger_articles_xml( \
        chemin_base, coll_articles, entree_texte, dates, autres_articles, \
        nouveaux_articles)
    
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
            autres_sections |= {(id, nom, etat_juridique, niveau, numero, \
                                 vigueur_debut, vigueur_fin, entree_texte.cid)}
        except Version_section.DoesNotExist:
            nouvelles_sections |= {(id, nom, etat_juridique, niveau, numero, \
                                    vigueur_debut, vigueur_fin, \
                                    entree_texte.cid)}
            dates |= {vigueur_debut, vigueur_fin}
        
        # Prise en compte des dates de vigueur
        #dates |= {vigueur_debut, vigueur_fin}
        
        # Continuer récursivement
        section_ta = lire_base_section_ta(chemin_base, url)
        
        dates, autres_sections, autres_articles, nouvelles_sections, \
            nouveaux_articles = ranger_sections_xml(chemin_base, \
            section_ta['LIEN_SECTION_TA'], section_ta['LIEN_ART'], \
            entree_texte, None, dates, autres_sections, autres_articles, \
            niv+1, nouvelles_sections, nouveaux_articles)
        
        # Affichage de l’avancement
        compteur_recursif()
    
    return dates, autres_sections, autres_articles, nouvelles_sections, \
           nouveaux_articles


def ranger_articles_xml(chemin_base, coll_articles, entree_texte, dates, \
                        autres_articles, nouveaux_articles):
    
    # Si pas d’article dans cette section
    if coll_articles == None:
        return dates, autres_articles, nouveaux_articles
    
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
            autres_articles |= {(id,  nom, etat_juridique, numero, \
                                 vigueur_debut, vigueur_fin, None, \
                                 entree_texte.cid)}
        except Version_article.DoesNotExist:
            nouveaux_articles |= {(id,  nom, etat_juridique, numero, \
                                   vigueur_debut, vigueur_fin, None, \
                                   entree_texte.cid)}
            dates |= {vigueur_debut, vigueur_fin}
        
        # Prise en compte des dates de vigueur
        #dates |= {vigueur_debut, vigueur_fin}
        
        # Affichage de l’avancement
        compteur_recursif()
    
    return dates, autres_articles, nouveaux_articles


def enregistrer_versions_texte(version, livraison, dates, autres_sections, autres_articles, entree_texte, nouvelles_sections, nouveaux_articles, chemin_base):
    
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
    
    def obtenir_travaux_articles(articles, chemin_base):
        for article in articles:
            yield {'version_article': article[0],
                   'texte': article[7],
                   'chemin': os.path.join(chemin_base, 'article', decompose_cid(article[0]+'.xml'))}
    
    # Import des enregistrements sections et articles
    # Il ne semble pas possible d’ajouter plus de 500 enregistrements
    #  par appel à insert_many, dont acte
    nouvelles_sections = list(nouvelles_sections)
    nouveaux_articles = list(nouveaux_articles)
    for i in range(0,int(math.ceil(len(nouvelles_sections)/tranches_bdd))):
        Version_section.insert_many(obtenir_sections(nouvelles_sections[i*tranches_bdd:(i+1)*tranches_bdd])).execute()
    for i in range(0,int(math.ceil(len(nouveaux_articles)/tranches_bdd))):
        Version_article.insert_many(obtenir_articles(nouveaux_articles[i*tranches_bdd:(i+1)*tranches_bdd])).execute()
    for i in range(0,int(math.ceil(len(nouveaux_articles)/tranches_bdd))):
        Travaux_articles.insert_many(obtenir_travaux_articles(nouveaux_articles[i*tranches_bdd:(i+1)*tranches_bdd], chemin_base)).execute()
    #Version_section.insert_many(obtenir_sections(nouvelles_sections)).execute()
    #Version_article.insert_many(obtenir_articles(nouveaux_articles)).execute()
    #Travaux_articles.insert_many(obtenir_travaux_articles(nouveaux_articles, chemin_base)).execute()
    
    # Remonter la dernière livraison (branche) jusqu’à la première
    # version commune avec cette nouvelle livraison
    entree_version_texte = None
    nouvelles_versions = set()
    if entree_texte.livraison:
        livraison_texte = Livraison_texte.select().where(
            Livraison_texte.livraison == entree_texte.livraison &
            Livraison_texte.texte == entree_texte
        ).order_by(Livraison_texte.version_texte.desc()).get()
        entree_version_texte = livraison_texte.version_texte
        
        # Cette boucle représente la première date de vigueur de la
        # nouvelle livraison. Réfléchir avec le croquis ci-dessous
        # en faisant varier N1 (N=nouveau) entre avant V1 et V3
        #    V1---------V2-----------V3-------V4-------V5
        #           N1-----------N2                   
        while not(entree_version_texte.vigueur_debut <= dates[0] and \
              comp_infini_strict(dates[0], entree_version_texte.vigueur_fin)):
            if entree_version_texte.version_prec == None:
                entree_version_texte = None
                break
            
            entree_version_texte = Version_texte.select().where(
                Version_texte.id == entree_version_texte.version_prec
            ).get()
        # TODO décider quoi faire si le titre ou une autre donnée
        #      mineure change -> nouvelle branche ? je dirais oui
        #      mais réfléchir finement, e.g. à etat_juridique
        if entree_version_texte != None and entree_version_texte.version_prec != None:
            entree_version_texte = Version_texte.select().where(
                Version_texte.id == entree_version_texte.version_prec
            ).get()
        
        # La première nouvelle version est à cheval entre deux
        # versions précédentes, il faut compléter l’intervalle VX-N1
        # J’imagine que ce cas ne doit jamais apparaître
        if entree_version_texte.vigueur_debut < dates[0] and \
           comp_infini_strict(dates[0], entree_version_texte.vigueur_fin):
            
            entree_version_texte = Version_texte.create(
                titre = version['TITRE'],
                titre_long = version['TITREFULL'],
                nature=version['NATURE'].lower(),
                date_texte=version['DATE_TEXTE'],
                date_publi=version['DATE_PUBLI'],
                date_modif=version['DERNIERE_MODIFICATION'],
                etat_juridique = version['ETAT'].lower(),
                vigueur_debut = entree_version_texte.vigueur_debut,
                vigueur_fin = dates[0],
                texte = entree_texte,
                version_prec=entree_version_texte
            )
            #nouvelles_versions |= {entree_version_texte}
            
            Livraison_texte.create(
                livraison = livraison,
                version_texte = entree_version_texte,
                texte = entree_texte
            )
            
            # TODO recopier les sections et articles de VX
            raise NonImplementeException()
    
    compteur_recursif(0, 0, True)
    
    for i in range(len(dates) - 1):
        
        compteur_recursif(i+1, len(dates)-1, True)
        
        # Enregistrement de cette version de texte #OK
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
            version_prec=entree_version_texte
        )
        nouvelles_versions |= {entree_version_texte}
        
        # Inscription du lien entre texte, livraison et version de texte #OK
        Livraison_texte.create(
            livraison = livraison,
            version_texte = entree_version_texte,
            texte = entree_texte
        )
        
        # Inscription du lien entre livraison et sections
        sections = list(set(nouvelles_sections) | autres_sections)
        sections = [section for section in sections if section[5] > entree_version_texte.vigueur_debut or comp_infini_strict(section[6], entree_version_texte.vigueur_fin)]
        
        def liste_sections(sections,version_texte):
            for section in sections:
                yield {'version_section': section[0],
                       'version_texte': version_texte}
        
        for i in range(0,int(math.ceil(len(sections)/tranches_bdd))):
            Liste_sections.insert_many(liste_sections(sections[i*tranches_bdd:(i+1)*tranches_bdd], entree_version_texte)).execute()
        
        # Inscription du lien entre livraison et articles
        articles = list(set(nouveaux_articles) | autres_articles)
        articles = [a for a in articles if a[4] > entree_version_texte.vigueur_debut or comp_infini_strict(a[5], entree_version_texte.vigueur_fin)]
        
        def liste_articles(articles,version_texte):
            for article in articles:
                yield {'version_article': article[0],
                       'version_texte': version_texte}
        
        for i in range(0,int(math.ceil(len(articles)/tranches_bdd))):
            Liste_articles.insert_many(liste_articles(articles[i*tranches_bdd:(i+1)*tranches_bdd], entree_version_texte)).execute()
        
        compteur_recursif()
    
    # Enregistrer cette livraison du texte comme étant calculée
    entree_texte.livraison = livraison
    entree_texte.save()


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

