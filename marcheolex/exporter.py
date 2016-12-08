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
from marcheolex import logger
from marcheolex import version_archeolex
from marcheolex.basededonnees import Texte
from marcheolex.basededonnees import Version_texte
from marcheolex.basededonnees import Version_section
from marcheolex.basededonnees import Article
from marcheolex.markdown import creer_markdown
from marcheolex.markdown import creer_markdown_texte
from marcheolex.utilitaires import normalisation_code
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import nop
from marcheolex.utilitaires import MOIS
from marcheolex.utilitaires import MOIS2
from marcheolex.utilitaires import comp_infini
from marcheolex.utilitaires import comp_infini_strict


def creer_historique(textes, format, dossier, cache):
    
    for texte in textes:
        creer_historique_texte(texte, format, dossier, cache)


def creer_historique_texte(texte, format, dossier, cache):
    
    # Créer le dossier si besoin
    sousdossier = '.'
    cid = texte[1]
    nom = texte[0] or cid
    
    path(dossier).mkdir_p()
    entree_texte = Texte.get(Texte.cid == cid)
    if entree_texte.nature in ('code', 'loi', 'ordonnance'):
        if not os.path.exists(os.path.join(dossier, entree_texte.nature+'s')):
            os.makedirs(os.path.join(dossier, entree_texte.nature+'s'))
        sousdossier = entree_texte.nature+'s'
    elif entree_texte.nature == 'decret':
        if not os.path.exists(os.path.join(dossier, u'décrets')):
            os.makedirs(os.path.join(dossier, u'décrets'))
        sousdossier = 'décrets'
    elif entree_texte.nature == 'arrete':
        if not os.path.exists(os.path.join(dossier, u'arrêtés')):
            os.makedirs(os.path.join(dossier, u'arrêtés'))
        sousdossier = 'arrêtés'
        
    if texte[2]:
        identifiant, nom_fichier = normalisation_code(nom)
        sousdossier = os.path.join('codes', identifiant)
        path(os.path.join(dossier, sousdossier)).mkdir_p()
        chemin_base = chemin_texte(cid, True)
    else:
        sousdossier = os.path.join(sousdossier, nom)
        nom_fichier = cid
    dossier = os.path.join(dossier, sousdossier)
    sousdossier = '.'
    if not os.path.exists(dossier):
        os.makedirs(dossier)
    fichier = os.path.join(dossier, nom_fichier + '.md')
    
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
    versions_texte = Version_texte.select().where(Version_texte.texte == texte[1])
    
    # Pour chaque version
    # - rechercher les sections et articles associés
    # - créer le fichier texte au format demandé
    # - commiter le fichier
    for (i_version, version_texte) in enumerate(versions_texte):
        
        # Passer les versions 'nulles'
        if version_texte.base is None:
            continue
        
        # Sélectionner les versions d’articles et sections présentes dans cette version de texte, c’est-à-dire celles créées avant et détruites après (ou jamais)
        articles =                                                                       \
            Article.select()                                                             \
                   .where(  (Article.texte == cid)                                       \
                          & (Article.debut <= version_texte.debut)                       \
                          & ((Article.fin >= version_texte.fin) | (Article.fin == None)) \
                         )
        
        versions_sections =                                                                              \
            Version_section.select()                                                                     \
                   .where(  (Version_section.texte == cid)                                               \
                          & (Version_section.debut <= version_texte.debut)                               \
                          & ((Version_section.fin >= version_texte.fin) | (Version_section.fin == None)) \
                         )
        
        # Créer l’en-tête
        date_fr = '{} {} {}'.format(version_texte.debut.day, MOIS2[int(version_texte.debut.month)], version_texte.debut.year)
        if version_texte.debut.day == 1:
            date_fr = '1er {} {}'.format(MOIS2[int(version_texte.debut.month)], version_texte.debut.year)
        contenu = nom + '\n'   \
                  + '\n'   \
                  + '- Date de consolidation : ' + date_fr + '\n'            \
                  + '- [Lien permanent Légifrance](http://legifrance.gouv.fr/affichCode.do?cidTexte=' + cid + '&dateTexte=' + str(version_texte.debut.year) + '{:02d}'.format(version_texte.debut.month) + '{:02d}'.format(version_texte.debut.day) + ')\n' \
                  + '\n' \
                  + '\n'
        
        # Créer les sections (donc tout le texte)
        contenu = creer_sections(contenu, 1, None, versions_sections, articles, version_texte, cid, cache)
        
        # Enregistrement du fichier
        f_texte = open(fichier, 'w')
        f_texte.write(contenu.encode('utf-8'))
        f_texte.close()
        
        # Exécuter Git
        date_base_legi = '{} {} {} {}:{}:{}'.format('18', 'juillet', '2014', '11', '30', '10') # TODO changer cela
        subprocess.call(['git', 'add', os.path.join(sousdossier, nom_fichier + '.md')], cwd=dossier)
        subprocess.call(['git', 'commit', '--author="Législateur <>"', '--date="' + str(version_texte.debut) + 'T00:00:00Z"', '-m', 'Version consolidée au {}\n\nVersions :\n- base LEGI : {}\n- programme Archéo Lex : {}'.format(date_fr, date_base_legi, version_archeolex), '-q', '--no-status'], cwd=dossier)
        
        if version_texte.fin == None:
            logger.info('Version {} enregistrée (du {} à maintenant)'.format(i_version, version_texte.debut))
        else:
            logger.info('Version {} enregistrée (du {} au {})'.format(i_version, version_texte.debut, version_texte.fin))


def creer_sections(texte, niveau, version_section_parente, versions_sections, articles, version_texte, cid, cache):
    
    marque_niveau = ''
    for i in range(niveau):
        marque_niveau = marque_niveau + '#'
    
    # Champ Version_section
    versions_section = versions_sections.select().where(Version_section.id_parent == version_section_parente).order_by(Version_section.numero)
    
    # Itérer sur les sections de cette section
    for version_section in versions_section:
        
        if comp_infini_strict(version_texte.debut, version_section.debut) or comp_infini_strict(version_section.fin, version_texte.fin):
            raise Exception('section non valide (version texte de {} à {}, version section de {} à {})'.format(version_texte.debut, version_texte.fin, version_section.debut, version_section.fin))
            return texte
        
        texte = texte                                                      \
                + marque_niveau + ' ' + version_section.nom.strip() + '\n' \
                + '\n'
        
        texte = creer_sections(texte, niveau+1, version_section, versions_sections, articles, version_texte, cid, cache)
        
        texte = creer_articles_section(texte, niveau, version_section, articles, version_texte, cid, cache)
    
    if len(versions_section) == 0:
        
        texte = creer_articles_section(texte, niveau, None, articles, version_texte, cid, cache)
    
    return texte


def creer_articles_section(texte, niveau, version_section_parente, articles, version_texte, cid, cache):
    
    marque_niveau = ''
    for i in range(niveau):
        marque_niveau = marque_niveau + '#'
    
    # Champ Article
    articles_section = articles.select().where(Article.version_section == version_section_parente)
    
    # Itérer sur les articles de cette section
    for article in articles_section:
        
        if comp_infini_strict(version_texte.debut, article.debut) or comp_infini_strict(article.fin, version_texte.fin):
            raise Exception('article non valide (version texte de {} à {}, version article de {} à {})'.format(version_texte.debut, version_texte.fin, article.debut, article.fin))
            continue
        
        chemin_markdown = os.path.join(cache, 'markdown', cid, article.id + '.md')
        f_article = open(chemin_markdown, 'r')
        texte_article = f_article.read().decode('utf-8')
        f_article.close()
        
        texte = texte                                                      \
                + marque_niveau + ' Article ' + article.num.strip() + '\n' \
                + '\n'                                                     \
                + texte_article + '\n'                                     \
                + '\n'                                                     \
                + '\n'
        
    return texte

