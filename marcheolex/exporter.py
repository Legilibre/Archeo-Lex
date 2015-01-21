# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module assemble les textes et fait l’export final
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
import subprocess
import datetime

from path import path
from bs4 import BeautifulSoup
from datetime import date, datetime

from marcheolex import logger
from marcheolex import version_archeolex
from marcheolex.basededonnees import Livraison
from marcheolex.basededonnees import Version_texte
from marcheolex.basededonnees import Version_section
from marcheolex.basededonnees import Version_article
from marcheolex.basededonnees import Livraison_texte
from marcheolex.basededonnees import Liste_sections
from marcheolex.basededonnees import Liste_articles
from marcheolex.markdown import creer_markdown
from marcheolex.markdown import creer_markdown_texte
from marcheolex.utilitaires import normalisation_code
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import nop
from marcheolex.utilitaires import MOIS
from marcheolex.utilitaires import MOIS2
from marcheolex.utilitaires import comp_infini
from marcheolex.utilitaires import comp_infini_strict


def creer_historique(livraison, textes, format, dossier, cache):
    
    for texte in textes:
        creer_historique_texte(livraison, texte, format, dossier, cache)


def creer_historique_texte(livraison, texte, format, dossier, cache):
    
    # Lecture des paramètres
    nom = texte[0]
    cid = texte[1]
    if not isinstance(livraison, datetime):
        livraison = datetime.strptime(livraison, '%Y%m%d-%H%M%S')
    
    # Rechercher les livraisons
    entree_livraison = Livraison.get(Livraison.date == livraison)
    
    # Créer le dossier si besoin
    sousdossier = '.'
    path(dossier).mkdir_p()
    path(os.path.join(dossier, 'codes')).mkdir_p()
    path(os.path.join(dossier, 'constitutions')).mkdir_p()
    path(os.path.join(dossier, 'lois')).mkdir_p()
    path(os.path.join(dossier, 'décrets')).mkdir_p()
    path(os.path.join(dossier, 'ordonnances')).mkdir_p()
    if texte[2]:
        identifiant, nom_fichier = normalisation_code(nom)
        dossier = os.path.join(dossier, 'codes', identifiant)
        sousdossier = '.'
        path(dossier).mkdir_p()
        path(os.path.join(dossier, sousdossier)).mkdir_p()
        chemin_base = chemin_texte(cid, True)
    fichier = os.path.join(dossier, sousdossier, nom_fichier + '.md')
    
    # Créer le dépôt Git
    if not os.path.exists(os.path.join(dossier, '.git')):
        subprocess.Popen(['git', 'init'], cwd=dossier)
    else:
        subprocess.Popen(['git', 'checkout', '--', sousdossier], cwd=dossier)
    
    if os.path.exists(fichier):
        raise Exception('Fichier existant : la mise à jour de fichiers existants n’est pas encore prise en charge.')
    
    # Vérifier que les articles ont été transformés en Markdown ou les créer le cas échéant
    creer_markdown_texte(texte, cache)
    
    # Sélection des versions du texte
    versions_texte = Version_texte.select(Version_texte, Livraison_texte).join(Livraison_texte).where((Livraison_texte.texte == texte[1]) & (Livraison_texte.livraison == entree_livraison)).execute()
    
    #print(versions_texte.count())
    # Pour chaque version
    # - rechercher les sections et articles associés
    # - créer le fichier texte au format demandé
    # - commiter le fichier
    for i_version, version_texte in enumerate(versions_texte):
        
        # Passer les versions 'nulles'
        #if version_texte.base is None:
        #    continue
        
        # Sélectionner les versions d’articles et sections présentes dans cette version de texte, c’est-à-dire celles créées avant et détruites après (ou jamais)
        articles = Version_article.select().join(Liste_articles, on=Liste_articles.version_article).where(Liste_articles.version_texte == version_texte)
        #    Version_article.select()                                                                             \
        #                   .where(  (Version_article.texte == cid)                                               \
        #                          & (Version_article.debut <= version_texte.debut)                               \
        #                          & ((Version_article.fin >= version_texte.fin) | (Version_article.fin == None)) \
        #                         )
        
        versions_sections = Version_section.select().join(Liste_sections, on=Liste_sections.version_section).where(Liste_sections.version_texte == version_texte)
        #versions_sections =                                                                              \
        #    Version_section.select()                                                                     \
        #           .where(  (Version_section.texte == cid)                                               \
        #                  & (Version_section.debut <= version_texte.debut)                               \
        #                  & ((Version_section.fin >= version_texte.fin) | (Version_section.fin == None)) \
        #                 )
        
        # Gérer les dates
        date_base_legi = str(livraison.day) + ' ' + MOIS2[int(livraison.month)] + livraison.strftime(' %Y %H:%M:%S')
        if livraison.day == 1:
            date_base_legi = '1er ' + MOIS2[int(livraison.month)] + livraison.strftime(' %Y %H:%M:%S')
        
        date_fr = str(version_texte.vigueur_debut.day) + ' ' + MOIS2[int(version_texte.vigueur_debut.month)] + ' ' + str(version_texte.vigueur_debut.year)
        if version_texte.vigueur_debut.day == 1:
            date_fr = '1er ' + MOIS2[int(version_texte.vigueur_debut.month)] + ' ' + str(version_texte.vigueur_debut.year)
        
        particule = 'au'
        date_git = str(version_texte.vigueur_debut)
        if version_texte.vigueur_debut == date(2222,2,22):
            date_git = '2099-01-01'
            particule = 'à une'
            date_fr = 'date indéterminée'
        
        # Créer l’en-tête
        
        contenu = nom + '\n'   \
                  + '\n'   \
                  + '- Date de consolidation : ' + date_fr + '\n'            \
                  + '- [Lien permanent Légifrance](http://legifrance.gouv.fr/affichCode.do?cidTexte=' + cid + '&dateTexte=' + str(version_texte.vigueur_debut.year) + '{:02d}'.format(version_texte.vigueur_debut.month) + '{:02d}'.format(version_texte.vigueur_debut.day) + ')\n' \
                  + '\n' \
                  + '\n'
        
        # Créer les sections (donc tout le texte)
        contenu = creer_sections(contenu, 1, None, versions_sections, articles, version_texte, cid, cache)
        
        # Enregistrement du fichier
        f_texte = open(fichier, 'w')
        f_texte.write(contenu.encode('utf-8'))
        f_texte.close()
        
        # Exécuter Git
        subprocess.call(['git', 'add', os.path.join(sousdossier, nom_fichier + '.md')], cwd=dossier)
        subprocess.call(['git', 'commit', '--author="Législateur <>"', '--date="' + date_git + 'T00:00:00Z"', '-m', 'Version consolidée {} {}\n\nVersions :\n- base LEGI : {}\n- programme Archéo Lex : {}'.format(particule, date_fr, date_base_legi, version_archeolex), '-q', '--no-status'], cwd=dossier, env={'GIT_COMMITTER_NAME': 'Législateur'.encode('utf-8'), 'GIT_COMMITTER_EMAIL': '', 'GIT_COMMITTER_DATE': date_git+'T00:00:00Z'})
        
        if version_texte.vigueur_debut == date(2222,2,22) and version_texte.vigueur_fin == None:
            logger.info('Version {} enregistrée (d’une date indéterminée à après)'.format(i_version+1))
        elif version_texte.vigueur_fin == date(2222,2,22):
            logger.info('Version {} enregistrée (du {} à une date indéterminée)'.format(i_version+1, version_texte.vigueur_debut))
        elif version_texte.vigueur_fin == None:
            logger.info('Version {} enregistrée (du {} à maintenant)'.format(i_version+1, version_texte.vigueur_debut))
        else:
            logger.info('Version {} enregistrée (du {} au {})'.format(i_version+1, version_texte.vigueur_debut, version_texte.vigueur_fin))
    
    # Ajouter un tag correspondant à la livraison
    subprocess.call(['git', 'tag', livraison.strftime('livraison-%Y-%m-%d-%H%M%S')], cwd=dossier)
    
    # Appeler git gc pour optimiser la taille du dépôt Git (généralement de l’ordre d’un facteur de 40 à 100)
    subprocess.call(['git', 'gc', '--aggressive'], cwd=dossier)


def creer_sections(texte, niveau, version_section_parente, versions_sections, articles, version_texte, cid, cache):
    
    marque_niveau = ''
    for i in range(niveau):
        marque_niveau = marque_niveau + '#'
    
    # Champ Version_section
    #versions_section = versions_sections.select().where(Version_section.id_parent == version_section_parente).order_by(Version_section.numero)
    #versions_section = versions_sections.select().where(Version_section.niveau == niveau).order_by(Version_section.numero)
    versions_section = Version_section.select().join(Liste_sections, on=Liste_sections.version_section).where(Liste_sections.id_parent == version_section_parente).where(Liste_sections.version_texte == version_texte).order_by(Version_section.numero).execute()
    
    # Itérer sur les sections de cette section
    for version_section in versions_section:
        
        #print('section {} (version texte {}) (version texte de {} à {}, version section de {} à {})'.format(version_section.id, version_texte.id, version_texte.vigueur_debut, version_texte.vigueur_fin, version_section.vigueur_debut, version_section.vigueur_fin))
        if comp_infini_strict(version_texte.vigueur_debut, version_section.vigueur_debut) or comp_infini_strict(version_section.vigueur_fin, version_texte.vigueur_fin):
            print('section {} (version texte {}) non valide (version texte de {} à {}, version section de {} à {})'.format(version_section.id, version_texte.id, version_texte.vigueur_debut, version_texte.vigueur_fin, version_section.vigueur_debut, version_section.vigueur_fin))
            raise Exception('section non valide (version texte de {} à {}, version section de {} à {})'.format(version_texte.vigueur_debut, version_texte.vigueur_fin, version_section.vigueur_debut, version_section.vigueur_fin))
            return texte
        
        # Gestion de la mention 'différé à une date indéterminée'
        differe = ''
        if version_section.vigueur_fin == date(2222,2,22):
            differe = ' [abrogation différée à une date indéterminée]'
        if version_section.vigueur_debut == date(2222,2,22):
            differe = ' [entrée en vigueur différée à une date indéterminée]'
        
        texte = texte                                                                \
                + marque_niveau + ' ' + version_section.nom.strip() + differe + '\n' \
                + '\n'
        
        #print(version_section.nom.strip() + ' ' + version_section.id)
        texte = creer_sections(texte, niveau+1, version_section.id, versions_sections, articles, version_texte, cid, cache)
        
        texte = creer_articles_section(texte, niveau, version_section.id, articles, version_texte, cid, cache)
    
    return texte


def creer_articles_section(texte, niveau, version_section_parente, articles, version_texte, cid, cache):
    
    marque_niveau = ''
    for i in range(niveau):
        marque_niveau = marque_niveau + '#'
    
    # Champ Version_article
    #articles_section = articles.select().where(Version_article.version_section == version_section_parente)
    #articles_section = articles.select().order_by(Version_article.numero)
    articles_section = Version_article.select().join(Liste_articles, on=Liste_articles.version_article).where(Liste_articles.id_parent == version_section_parente).where(Liste_articles.version_texte == version_texte).order_by(Version_article.numero)
    
    # Itérer sur les articles de cette section
    for article in articles_section:
        
        if comp_infini_strict(version_texte.vigueur_debut, article.vigueur_debut) or comp_infini_strict(article.vigueur_fin, version_texte.vigueur_fin):
            raise Exception('article non valide (version texte de {} à {}, version article de {} à {})'.format(version_texte.vigueur_debut, version_texte.vigueur_fin, article.vigueur_debut, article.vigueur_fin))
            continue
        
        chemin_markdown = os.path.join(cache, 'markdown', cid, article.id + '-' + article.condensat + '.md')
        f_article = open(chemin_markdown, 'r')
        texte_article = f_article.read().decode('utf-8')
        f_article.close()
        
        # Gestion de la mention 'différé à une date indéterminée'
        differe = ''
        if article.vigueur_fin == date(2222,2,22):
            differe = ' [abrogation différée à une date indéterminée]'
        if article.vigueur_debut == date(2222,2,22):
            differe = ' [entrée en vigueur différée à une date indéterminée]'
        
        texte = texte                                                                \
                + marque_niveau + ' Article ' + article.nom.strip() + differe + '\n' \
                + '\n'                                                               \
                + texte_article + '\n'                                               \
                + '\n'                                                               \
                + '\n'
        
    return texte

