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
            'class': 'logging.NullHandler',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'peewee': {
            'handlers': ['null'],
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'propagate': True,
        }
    }
}

dictConfig(LOGGING)

logger = logging.getLogger(__name__)

version_archeolex = '0.3.0-alpha';


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

natures = {
    'CONSTITUTION': u'constitution',
    'LOI_CONSTIT': u'loi constitutionnelle',
    'LOI_ORGANIQUE': u'loi organique',
    'LOI': u'loi',
    'CODE': u'code',
    'ORDONNANCE': u'ordonnance',
    'DECRET_LOI': u'décret-loi',
    'DECRET': u'décret',
    'CONVENTION': u'convention',
    'ARRETE': u'arrêté',
    'CIRCULAIRE': u'circulaire',
    'DECISION': u'décision',
    'DECLARATION': u'déclaration'
}


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

'''
class (Exception):
    pass
'''

# vim: set ts=4 sw=4 sts=4 et:
