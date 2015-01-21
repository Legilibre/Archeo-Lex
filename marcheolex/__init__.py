# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce fichier sert de base au module et gère la journalisation
# 
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# the LICENSE file for more details.

# Imports
import logging
from logging.config import dictConfig

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'peewee': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

dictConfig(LOGGING)

logger = logging.getLogger(__name__)

version_archeolex = '0.2.0-alpha';


#
# Constantes
#

# Bases gérées
bases = ['LEGI'] #['JORF', 'LEGI', 'KALI', 'CNIL', 'CONSTIT']

# Adresses des serveurs et noms des fichiers
# Voir http://rip.journal-officiel.gouv.fr/index.php/pages/juridiques
serveurs = {
    'JORF': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'jorf', 'open1234', '/'),
    'LEGI': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'legi', 'open1234', '/'),
    'KALI': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'kali', 'open1234', '/'),
    'CNIL': ('ftp', 'ftp2.journal-officiel.gouv.fr', 'cnil', 'open1234', '/'),
    'CONSTIT': ('ftp', 'ftp2.journal-officiel.gouv.fr', \
                'constit', 'open1234', '/'),
    'CIRCULAIRES': ('ftp', 'echanges.dila.gouv.fr:6370', \
                    'anonymous', '', '/CIRCULAIRES/FLUX/'),
}
fichiers_fond = {
    'JORF': 'Freemium_jorf_global_%Y%m%d-%H%M%S.tar.gz',
    'LEGI': 'Freemium_legi_global_%Y%m%d-%H%M%S.tar.gz',
    'KALI': 'Freemium_kali__%Y%m%d-%H%M%S.tar\.gz',
    'CNIL': 'Freemium_cnil_global_%Y%m%d-%H%M%S.tar.gz',
    'CONSTIT': 'Freemium_constit_global_%Y%m%d-%H%M%S.tar.gz',
    'CIRCULAIRES': None
}
fichiers_majo = {
    'JORF': 'jorf_%Y%m%d-%H%M%S.tar.gz',
    'LEGI': 'legi_%Y%m%d-%H%M%S.tar.gz',
    'KALI': 'kali_%Y%m%d-%H%M%S.tar.gz',
    'CNIL': 'cnil_%Y%m%d-%H%M%S.tar.gz',
    'CONSTIT': 'constit_%Y%m%d-%H%M%S.tar.gz',
    'CIRCULAIRES': 'circulaire_%d%m%Y%Hh%M.tar.gz'
}

# Tranches d’insertion dans la base de données, semble fixé par Peewee
# Changer cette valeur peut bloquer le déroulement du programme, sauf
# évolution de Peewee
tranches_bdd = 500

# Taille du condensat tronqué pour indexer le cache des articles
# Noter qu’un chiffre supplémentaire est ajouté si jamais deux
# mêmes articles ont le même condensat tronqué
condensat_tronque = 4


#
# Exceptions
#

class NonImplementeException(Exception):
    pass

class NomBaseException(Exception):
    pass

class FondationNonUniqueException(Exception):
    pass

class FondationNonTrouveeException(Exception):
    pass

class FichierNonExistantException(Exception):
    pass

'''
class (Exception):
    pass
'''

