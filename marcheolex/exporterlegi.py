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
import time
from path import Path
from bs4 import BeautifulSoup
import legi
import legi.utils
from marcheolex import logger
from marcheolex import version_archeolex
from marcheolex.markdownlegi import creer_markdown
from marcheolex.markdownlegi import creer_markdown_texte
from marcheolex.utilitaires import normalisation_code
from marcheolex.utilitaires import chemin_texte
from marcheolex.utilitaires import nop
from marcheolex.utilitaires import MOIS
from marcheolex.utilitaires import MOIS2
from marcheolex.utilitaires import comp_infini
from marcheolex.utilitaires import comp_infini_strict


def creer_historique_legi(textes, format, dossier, cache, bdd):
    
    for texte in textes:
        creer_historique_texte(texte, format, dossier, cache, bdd)


def creer_historique_texte(texte, format, dossier, cache, bdd):

    # Connexion à la base de données
    #print(bdd)
    db = legi.utils.connect_db(bdd)

    # Créer le dossier si besoin
    sousdossier = '.'
    cid = texte[1]
    nom = texte[0] or cid

    Path(dossier).mkdir_p()
    entree_texte = db.one("""
        SELECT id, nature, titre, titrefull, etat, date_debut, date_fin
        FROM textes_versions
        WHERE id = '{0}'
    """.format(cid))
    if entree_texte[1].lower() in ('code', 'loi', 'ordonnance'):
        if not os.path.exists(os.path.join(dossier, entree_texte[1].lower()+'s')):
            os.makedirs(os.path.join(dossier, entree_texte[1].lower()+'s'))
        sousdossier = entree_texte[1].lower()+'s'
    elif entree_texte[1].lower() == 'decret':
        if not os.path.exists(os.path.join(dossier, u'décrets')):
            os.makedirs(os.path.join(dossier, u'décrets'))
        sousdossier = 'décrets'
    elif entree_texte[1].lower() == 'arrete':
        if not os.path.exists(os.path.join(dossier, u'arrêtés')):
            os.makedirs(os.path.join(dossier, u'arrêtés'))
        sousdossier = 'arrêtés'
        
    if texte[2]:
        identifiant, nom_fichier = normalisation_code(nom)
        sousdossier = os.path.join('codes', identifiant)
        Path(os.path.join(dossier, sousdossier)).mkdir_p()
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
        subprocess.call(['git', 'init'], cwd=dossier)
    else:
        subprocess.call(['git', 'checkout', '--', sousdossier], cwd=dossier)
    
    if os.path.exists(fichier):
        raise Exception('Fichier existant : la mise à jour de fichiers existants n’est pas encore prise en charge.')

    # Vérifier que les articles ont été transformés en Markdown ou les créer le cas échéant
    creer_markdown_texte(texte, db, cache)
    
    # Sélection des versions du texte
    versions_texte_db = db.all("""
          SELECT debut
          FROM sommaires
          WHERE cid = '{0}'
        UNION
          SELECT fin
          FROM sommaires
          WHERE cid = '{0}'
    """.format(cid, cid))
    dates_texte = []
    versions_texte = []
    for vt in versions_texte_db:
        vt = vt[0]
        if isinstance(vt, basestring):
            vt = datetime.date(*(time.strptime(vt, '%Y-%m-%d')[0:3]))
        dates_texte.append( vt )
    for i in range(0,len(dates_texte)-1):
        debut = dates_texte[i]
        fin = dates_texte[i+1]
        versions_texte.append( (debut, fin) )
    
    sql_texte = "cid = '{0}'".format(cid)

    # Pour chaque version
    # - rechercher les sections et articles associés
    # - créer le fichier texte au format demandé
    # - commiter le fichier
    for (i_version, version_texte) in enumerate(versions_texte):
        
        # Passer les versions 'nulles'
        #if version_texte.base is None:
        #    continue

        sql = sql_texte + " AND debut <= '{0}' AND ( fin >= '{1}' OR fin == '2999-01-01' )".format(version_texte[0], version_texte[1])

        # Créer l’en-tête
        date_fr = '{} {} {}'.format(version_texte[0].day, MOIS2[int(version_texte[0].month)], version_texte[0].year)
        if version_texte[0].day == 1:
            date_fr = '1er {} {}'.format(MOIS2[int(version_texte[0].month)], version_texte[0].year)
        contenu = nom + '\n'   \
                  + '\n'   \
                  + '- Date de consolidation : ' + date_fr + '\n'            \
                  + '- [Lien permanent Légifrance](http://legifrance.gouv.fr/affichCode.do?cidTexte=' + cid + '&dateTexte=' + str(version_texte[0].year) + '{:02d}'.format(version_texte[0].month) + '{:02d}'.format(version_texte[0].day) + ')\n' \
                  + '\n' \
                  + '\n'

        # Enregistrement du fichier
        if format['organisation'] != 'fichier-unique':
            f_texte = open('README.md', 'w')
            f_texte.write(contenu.encode('utf-8'))
            f_texte.close()

            # Retrait des fichiers des anciennes versions
            subprocess.call('rm *.md', cwd=dossier, shell=True)

        # Créer les sections (donc tout le texte)
        contenu = creer_sections(contenu, 1, None, version_texte, sql, [], format, dossier, db, cache)
        
        # Enregistrement du fichier
        if format['organisation'] == 'fichier-unique':
            f_texte = open(fichier, 'w')
            f_texte.write(contenu.encode('utf-8'))
            f_texte.close()
        
        # Exécuter Git
        date_base_legi = '{} {} {} {}:{}:{}'.format('18', 'juillet', '2014', '11', '30', '10') # TODO changer cela
        subprocess.call(['git', 'add', '.'], cwd=dossier)
        subprocess.call(['git', 'commit', '--author="Législateur <>"', '--date="' + str(version_texte[0]) + 'T00:00:00Z"', '-m', 'Version consolidée au {}\n\nVersions :\n- base LEGI : {}\n- programme Archéo Lex : {}'.format(date_fr, date_base_legi, version_archeolex), '-q', '--no-status'], cwd=dossier)
        
        if version_texte[1] == None:
            logger.info('Version {} enregistrée (du {} à maintenant)'.format(i_version+1, version_texte[0]))
        else:
            logger.info('Version {} enregistrée (du {} au {})'.format(i_version+1, version_texte[0], version_texte[1]))


def creer_sections(texte, niveau, parent, version_texte, sql, arborescence, format, dossier, db, cache):
 
    #print(parent)

    marque_niveau = ''
    for i in range(niveau):
        marque_niveau = marque_niveau + '#'

    sql_section_parente = "parent = '{0}'".format(parent)
    if parent == None:
        sql_section_parente = "parent IS NULL OR parent = ''"

    toutes_sections = db.all("""
        SELECT *
        FROM sommaires
        WHERE ({0})
          AND ({1})
        ORDER BY position
    """.format(sql_section_parente, sql))

    sections = []
    articles = []

    # Itérer sur les sections de cette section
    for section in toutes_sections:

        #id, section, num, date_debut, date_fin, bloc_textuel, cid = article
        rcid, rparent, relement, rdebut, rfin, retat, rnum, rposition, r_source = section
        #print(relement)
        #print(rnum)

        if comp_infini_strict(version_texte[0], rdebut) or comp_infini_strict(rfin, version_texte[1]):
            raise Exception(u'section non valide (version texte de {} a {}, version section de {} à {})'.format(version_texte[0], version_texte[1], rdebut, rfin))
            return texte

        # L’élément est un titre de sommaire, rechercher son texte et l’ajouter à la liste
        if relement[4:8] == 'SCTA':
            tsection = db.one("""
                SELECT titre_ta, commentaire
                FROM sections
                WHERE id='{0}'
            """.format(relement))
            sections.append( (relement, tsection[0].strip()) )

        # L’élément est un article, l’ajouter à la liste
        elif relement[4:8] == 'ARTI':
            articles.append( relement )

    if len(sections) > 0 and len(articles) > 0:
        print('La section '+parent+'a a la fois des articles et des sections')

    if len(articles):
        texte = creer_articles_section(texte, niveau, articles, version_texte, arborescence, format, dossier, db, cache)

    for section in sections:
        rarborescence = arborescence
        rarborescence.append( section )
        texte = texte                                  \
                + marque_niveau + ' ' + section[1] + '\n' \
                + '\n'
        texte = creer_sections(texte, niveau+1, section[0], version_texte, sql, rarborescence, format, dossier, db, cache)

    return texte


#def creer_sections(texte, niveau, parent, version_texte, sql, arborescence, format, dossier, db, cache):
#def creer_articles_section(texte, niveau, version_section_parente, articles, version_texte, cid, format, sections, dossier, cache):
def creer_articles_section(texte, niveau, articles, version_texte, arborescence, format, dossier, db, cache):

    marque_niveau = ''
    for i in range(niveau):
        marque_niveau = marque_niveau + '#'

    textes_articles = db.all("""
        SELECT id, section, num, date_debut, date_fin, bloc_textuel, cid
        FROM articles
        WHERE id IN ('{0}')
    """.format("','".join(articles)))
    darticles = {}

    # Itérer sur les articles de cette section
    for article in textes_articles:
        
        id, section, num, date_debut, date_fin, bloc_textuel, cid = article
        #print(num)
        #print(bloc_textuel)
        #print(section)
        #print(version_section_parente)
        #print(version_texte[0])
        #print(date_debut)
        #print(version_texte[1])
        #print(date_fin)

        if comp_infini_strict(version_texte[0], date_debut) or comp_infini_strict(date_fin, version_texte[1]):
            continue

        darticles[id] = (num.strip(), bloc_textuel)

    for article in articles:
        chemin_markdown = os.path.join(cache, 'markdown', cid, article + '.md')
        f_article = open(chemin_markdown, 'r')
        texte_article = f_article.read().decode('utf-8')
        f_article.close()
        
        texte = texte                                                        \
                + marque_niveau + ' Article ' + darticles[article][0] + '\n' \
                + '\n'                                                       \
                + texte_article + '\n'                                       \
                + '\n'                                                       \
                + '\n'

        # Format « 1 dossier = 1 article »
        fichier = os.path.join(dossier, darticles[article][0] + '.md')
        if format['organisation'] == 'repertoires-simple':
            texte_article = texte_article + '\n'
            f_texte = open(fichier, 'w')
            f_texte.write(texte_article.encode('utf-8'))
            f_texte.close()
        
    return texte

# vim: set ts=4 sw=4 sts=4 et:
