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
from marcheolex.basededonnees import Texte
from marcheolex.basededonnees import Version_texte
from marcheolex.basededonnees import Section
from marcheolex.basededonnees import Version_section
from marcheolex.basededonnees import Article
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import normalise_date
from marcheolex.utilitaires import comp_infini


def ranger(textes, cache):
    
    for texte in textes:
        
        lire_code_xml(texte, cache)


def lire_code_xml(cle, cache):
    
    if not cle[2]:
        return
    
    cidTexte = cle[1]
    chemin_base = os.path.join(cache, 'bases-xml', chemin_texte(cidTexte))
    if not os.path.exists(chemin_base):
        raise Exception()
    
    # Lire les informations sur le texte
    ranger_texte_xml(chemin_base, cidTexte, 'code')


# Vérifier si le texte existe, et en fonction de cela ajouter ou mettre à jour
def ranger_texte_xml(chemin_base, cidTexte, nature_attendue=None):
    
    # Lecture brute du fichier XML texte/version
    chemin_texte_version = os.path.join(chemin_base, 'texte', 'version', cidTexte + '.xml')
    if not os.path.exists(chemin_texte_version):
        raise Exception()
    f_version = open(chemin_texte_version, 'r')
    soup_version = BeautifulSoup(f_version.read(), 'xml')
    version_META = soup_version.find('META')
    version_META_COMMUN = version_META.find('META_COMMUN')
    version_META_SPEC = version_META.find('META_SPEC')
    version_META_TEXTE_CHRONICLE = version_META_SPEC.find('META_TEXTE_CHRONICLE')
    version_META_TEXTE_VERSION = version_META_SPEC.find('META_TEXTE_VERSION')
    
    version_NATURE = version_META_COMMUN.find('NATURE').text
    version_CID = version_META_TEXTE_CHRONICLE.find('CID').text
    version_NOR = version_META_TEXTE_CHRONICLE.find('NOR').text
    version_DATE_TEXTE = version_META_TEXTE_CHRONICLE.find('DATE_TEXTE').text
    version_DATE_PUBLI = version_META_TEXTE_CHRONICLE.find('DATE_PUBLI').text
    version_TITRE = version_META_TEXTE_VERSION.find('TITRE').text
    version_TITREFULL = version_META_TEXTE_VERSION.find('TITREFULL').text
    version_DATE_DEBUT = version_META_TEXTE_VERSION.find('DATE_DEBUT').text
    version_DATE_FIN = version_META_TEXTE_VERSION.find('DATE_FIN').text
    version_ETAT = version_META_TEXTE_VERSION.find('ETAT').text
    
    # Lecture brute du fichier XML texte/struct
    chemin_texte_struct = os.path.join(chemin_base, 'texte', 'struct', cidTexte + '.xml')
    if not os.path.exists(chemin_texte_struct):
        raise Exception()
    f_struct = open(chemin_texte_struct, 'r')
    soup_struct = BeautifulSoup(f_struct.read(), 'xml')
    struct_META = soup_struct.find('META')
    struct_META_COMMUN = struct_META.find('META_COMMUN')
    struct_META_SPEC = struct_META.find('META_SPEC')
    struct_META_TEXTE_CHRONICLE = struct_META_SPEC.find('META_TEXTE_CHRONICLE')
    struct_META_TEXTE_VERSION = struct_META_SPEC.find('META_TEXTE_VERSION')
    struct_VERSIONS = soup_struct.find('VERSIONS')
    struct_STRUCT = soup_struct.find('STRUCT')
    
    struct_NATURE = struct_META_COMMUN.find('NATURE').text
    struct_CID = struct_META_TEXTE_CHRONICLE.find('CID').text
    struct_NOR = struct_META_TEXTE_CHRONICLE.find('NOR').text
    struct_DATE_TEXTE = struct_META_TEXTE_CHRONICLE.find('DATE_TEXTE').text
    struct_DATE_PUBLI = struct_META_TEXTE_CHRONICLE.find('DATE_PUBLI').text
    struct_VERSION = struct_VERSIONS.find_all('VERSION')
    struct_VERSION_etat = struct_VERSION[0]['etat']
    struct_LIEN_TXT = struct_VERSION[0].find('LIEN_TXT')
    struct_LIEN_TXT_id = struct_LIEN_TXT['id']
    struct_LIEN_TXT_debut = struct_LIEN_TXT['debut']
    struct_LIEN_TXT_fin = struct_LIEN_TXT['fin']
    struct_LIEN_ART = struct_STRUCT.find_all('LIEN_ART')
    struct_LIEN_SECTION_TA = struct_STRUCT.find_all('LIEN_SECTION_TA')
    
    # Traitements de base
    version_DATE_TEXTE = normalise_date(version_DATE_TEXTE)
    version_DATE_PUBLI = normalise_date(version_DATE_PUBLI)
    version_DATE_DEBUT = normalise_date(version_DATE_DEBUT)
    version_DATE_FIN = normalise_date(version_DATE_FIN)
    struct_DATE_TEXTE = normalise_date(struct_DATE_TEXTE)
    struct_DATE_PUBLI = normalise_date(struct_DATE_PUBLI)
    
    # Vérifications
    if not cidTexte == version_CID:
        raise Exception()
    if nature_attendue and not version_NATURE == nature_attendue.upper() or not struct_NATURE == nature_attendue.upper():
        raise Exception()
    if not version_DATE_TEXTE == struct_DATE_TEXTE:
        raise Exception()
    if not version_DATE_PUBLI == struct_DATE_PUBLI:
        raise Exception()
    if not len(struct_VERSION) == 1:  # texte/version ne peut avoir qu’une seule version, donc texte/struct également et elles doivent correspondre
        raise Exception()
    
    # Enregistrement du Texte
    # TODO gérer les mises à jour
    try:
        entree_texte = Texte.get(Texte.cid == version_CID)
    except:
        entree_texte = Texte.create(
            cid=version_CID.upper(),
            nor=version_NOR.upper(),
            nature=version_NATURE.lower(),
            date_publi=version_DATE_PUBLI,
            date_texte=version_DATE_TEXTE,
        )
    
    # Enregistrement de la Version_texte d’autorité
    # TODO gérer les mises à jour
    try:
        entree_version_texte = Version_texte.get(Version_texte.texte == entree_texte)
    except:
        entree_version_texte = Version_texte.create(
            texte=entree_texte,
            titre=version_TITRE,
            titre_long=version_TITREFULL,
            etat_juridique=version_ETAT.lower(),
            debut=version_DATE_DEBUT,
            fin=version_DATE_FIN,
            base=None
        )
    
    # Recensement des dates de changement
    dates_changement = set([version_DATE_DEBUT, version_DATE_FIN])
    ensemble_versions_sections = set()
    ensemble_articles = set()
    
    # Ajouter récursivement les sections et articles
    dates_changement, ensemble_versions_section, ensemble_articles = ranger_sections_xml(chemin_base, struct_LIEN_SECTION_TA, struct_LIEN_ART, entree_texte, entree_version_texte, None, None, dates_changement, ensemble_versions_sections, ensemble_articles, cidTexte, 1)
    print('')
    
    # Créer les versions de textes
    dates_changement = list(dates_changement)
    dates_changement.sort(cmp=comp_infini)
    for i in range(len(dates_changement) - 1):
        # TODO gérer les mises à jour
        Version_texte.create(
            texte=entree_texte,
            titre=version_TITRE,
            titre_long=version_TITREFULL,
            etat_juridique=version_ETAT.lower(),
            debut=dates_changement[i],
            fin=dates_changement[i+1],
            base=entree_version_texte
        )


# Parcourir récursivement les sections
# - enregistrer celles du niveau N (N≥1)
# - ouvrir les fichiers correspondant à ces sections
# - appeler ranger_sections_xml sur les nœuds de STRUCTURE_TA
def ranger_sections_xml(chemin_base, coll_sections, coll_articles, entree_texte, entree_version_texte, section_parente, version_section_parente, dates_changement, ensemble_versions_sections, ensemble_articles, cidTexte, niv):
    
    # Prévenir les récursions infinies - les specs indiquent un max de 10
    if niv == 11:
        raise Exception()
    
    # Traiter les articles à ce niveau
    dates_changement, ensemble_articles = ranger_articles_xml(chemin_base, coll_articles, version_section_parente, entree_texte, entree_version_texte, dates_changement, ensemble_articles, cidTexte)
    
    for i in range(len(coll_sections)):
        
        print('{}/{}'.format(i+1, len(coll_sections)), end='')
        sys.stdout.flush()
        
        cid = coll_sections[i]['cid']
        id = coll_sections[i]['id']
        nom = coll_sections[i].text
        etat_juridique = coll_sections[i]['etat']
        niveau = coll_sections[i]['niv']
        debut = normalise_date(coll_sections[i]['debut'])
        fin = normalise_date(coll_sections[i]['fin'])
        url = coll_sections[i]['url'][1:]
        numero = i+1
        
        # Enregistrement de la section
        try:
            entree_section = Section.get(Section.cid == cid)
        except:
            entree_section = Section.create(
                cid=cid,
                cid_parent=section_parente,
                niveau=niveau,
                texte=entree_texte
            )
        
        # Ajout des dates limites pour préparer l’édition de liens
        dates_changement |= {debut, fin}
        
        # Enregistrement de version de section
        # TODO gérer les mises à jour
        try:
            entree_version_section = Version_section.get(Version_section.id == id)
        except:
            entree_version_section = Version_section.create(
                cid=cid,
                id=id,
                id_parent=version_section_parente,
                nom=nom,
                etat_juridique=etat_juridique,
                niveau=niveau,
                numero=numero,
                debut=debut,
                fin=fin,
                texte=entree_texte,
                version_texte=entree_version_texte
            )
        
        # Ajout de cette version de section
        ensemble_versions_sections |= {entree_version_section}
        
        print(' → ', end='')
        sys.stdout.flush()
        
        # Continuer récursivement
        chemin_section_ta = os.path.join(chemin_base, 'section_ta', url)
        f_section_ta = open(chemin_section_ta, 'r')
        soup = BeautifulSoup(f_section_ta.read(), 'xml')
        section_ta_STRUCTURE_TA = soup.find('STRUCTURE_TA')
        section_ta_LIEN_SECTION_TA = section_ta_STRUCTURE_TA.find_all('LIEN_SECTION_TA')
        section_ta_LIEN_ART = section_ta_STRUCTURE_TA.find_all('LIEN_ART')
        
        dates_changement, ensemble_versions_sections, ensemble_articles = ranger_sections_xml(chemin_base, section_ta_LIEN_SECTION_TA, section_ta_LIEN_ART, entree_texte, entree_version_texte, entree_section, entree_version_section, dates_changement, ensemble_versions_sections, ensemble_articles, cidTexte, niv+1)
        
        print('\033[3D   \033[3D', end='')
        
        nb_chiffres=len('{}/{}'.format(i+1, len(coll_sections)))
        print('\033[' + str(nb_chiffres) + 'D' + (''.join([' ' * nb_chiffres])) + '\033[' + str(nb_chiffres) + 'D', end='')
    
    return dates_changement, ensemble_versions_sections, ensemble_articles


def ranger_articles_xml(chemin_base, coll_articles, entree_version_section, entree_texte, entree_version_texte, dates_changement, ensemble_articles, cidTexte):
    
    if coll_articles == None:
        return dates_changement, ensemble_articles
    
    for i in range(len(coll_articles)):
        
        print('({}/{})'.format(i+1, len(coll_articles)), end='')
        sys.stdout.flush()
        
        # Lecture brute des attributs XML
        id = coll_articles[i]['id']
        nom = coll_articles[i].text
        etat_juridique = coll_articles[i]['etat']
        num = coll_articles[i]['num']
        debut = normalise_date(coll_articles[i]['debut'])
        fin = normalise_date(coll_articles[i]['fin'])
        
        # Enregistrement de l’article
        # TODO gérer les mises à jour
        try:
            entree_article = Article.get(Article.id == id)
        except:
            entree_article = Article.create(
                id=id,
                nom=nom,
                etat_juridique=etat_juridique,
                num=num,
                debut=debut,
                fin=fin,
                texte=entree_texte,
                version_section=entree_version_section,
                version_texte=entree_version_texte
            )
        
        # Inscription des dates et articles
        dates_changement |= {debut, fin}
        ensemble_articles |= {entree_article}
        
        nb_chiffres=len('({}/{})'.format(i+1, len(coll_articles)))
        print('\033[' + str(nb_chiffres) + 'D' + (''.join([' ' * nb_chiffres])) + '\033[' + str(nb_chiffres) + 'D', end='')
        sys.stdout.flush()
    
    return dates_changement, ensemble_articles

