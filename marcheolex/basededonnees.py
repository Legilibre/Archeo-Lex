# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module gère la structure de la base de données
# 
# La version de la base de données manipulée ici est : 2.1
# Cette version est incrémentée à chaque changement de la BDD.
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

from path import path
from peewee import Model
from peewee import Proxy
from peewee import SqliteDatabase
from peewee import BlobField
from peewee import BooleanField
from peewee import CharField
from peewee import DateField
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import IntegerField


# Initialisation de la base de données
database_proxy = Proxy()


## Définition des classes représentant les articles, textes et leur versionnement

class BaseModel(Model):
    
    class Meta:
        
        database = database_proxy

# Classe représentant une livraison d’une base

class Livraison(BaseModel):
    
    date = DateTimeField(primary_key=True) # date de la livraison
    type = CharField(max_length=9) # 'fondation' ou 'miseajour' (fondation = dump complet, miseajour = dump incrémental)
    base = CharField(max_length=4) # 'LEGI', etc.
    precedente = ForeignKeyField('self', null=True, related_name='livraison_precedente') # si type='miseajour', date de la livraison précédente
    suivante = ForeignKeyField('self', null=True, related_name='livraison_suivante') # date de la livraison précédente le cas échéant
    fondation = ForeignKeyField('self', null=True, related_name='livraison_fondation') # si type='miseajour', date de la livraison fondation


# Classe représentant un texte

class Texte(BaseModel):
    
    enum_natures = [
        ('constitution', 'Constitution'),
        ('code', 'Code'),
        ('loi', 'Loi'),
        ('loi constitutionnelle', 'Loi constitutionnelle'),
        ('ordonnance', 'Ordonnance'),
        ('décret', 'Décrêt'),
        ('arrêté', 'Arrêté'),
        ('décret-loi', 'Décret-loi')
    ]
    
    cid = CharField(max_length=20, primary_key=True) # identifiant technique cid
    nor = CharField(max_length=20, null=True) # identifiant NOR
    base = CharField(max_length=4) # 'LEGI', etc.
    livraison = ForeignKeyField(Livraison, null=True) # dernière livraison enregistrée pour ce texte


# Classe représentant une version d’un texte

class Version_texte(BaseModel):
    
    enum_etats_juridiques = [
        ('VIGUEUR', 'vigueur'),
        ('VIGUEUR_DIFF', 'vigueur différée'),
        ('ABROGE', 'abrogé'),
        ('ABROGE_DIFF', 'abrogé différé'),
        ('ANNULE', 'annulé'),
        ('PERIME', 'périmé'),
        ('TRANSFERE', 'transféré'),
        ('', 'disjoint'),
        ('', 'substitué'),
        ('MODIFIE', ''),
        ('MODIFIE_MORT_NE', '')
    ]
    
    enum_natures = [
        ('constitution', 'Constitution'),
        ('code', 'Code'),
        ('loi', 'Loi'),
        ('loi constitutionnelle', 'Loi constitutionnelle'),
        ('ordonnance', 'Ordonnance'),
        ('décret', 'Décrêt'),
        ('arrêté', 'Arrêté'),
        ('décret-loi', 'Décret-loi')
    ]
    
    #id = IntegerField(primary_key=True) # identifiant non-significatif id
    titre = CharField(max_length=200) # titre (court) du texte
    titre_long = CharField(max_length=200) # titre (long) du texte
    nature = CharField(max_length=20, choices=enum_natures) # nature du texte, 'code' pour l’instant
    date_texte = DateField(null=True) # date de signature du texte
    date_publi = DateField(null=True) # date de publication du texte (au JORF)
    date_modif = DateField(null=True) # date de la dernière modification (éditoriale) du texte
    etat_juridique = CharField(max_length=25) # état juridique du texte au moment de la livraison
    vigueur_debut = DateField() # date d’entrée en vigueur de cette version de texte
    vigueur_fin = DateField(null=True) # date de fin de vigueur de cette version de texte
    version_prec = ForeignKeyField('self', null=True) # version précédente en vigueur dans cette branche de livraison
    texte = ForeignKeyField(Texte) # texte auquel est rattachée cette version de texte


# Classe représentant une version d’une section

class Version_section(BaseModel):
    
    id = CharField(max_length=20, primary_key=True) # identifiant technique id
    id_parent = ForeignKeyField('self', null=True) # parent hiérarchique de cette section
    nom = CharField(max_length=200) # titre de la section
    etat_juridique = CharField(max_length=25) # état juridique de la section au moment de la livraison
    niveau = IntegerField() # niveau hiérarchique du titre
    numero = IntegerField() # numéro/index de ce titre dans son niveau hiérarchique
    vigueur_debut = DateField() # date d’entrée en vigueur de cette version de section
    vigueur_fin = DateField(null=True) # date de fin de vigueur de cette version de section
    texte = ForeignKeyField(Texte) # texte auquel est rattachée cette version de section


# Classe représentant une version d’un article

class Version_article(BaseModel):
    
    enum_etat_juridique = [
        'vigueur',
        'vigueur différée',
        'abrogé',
        'vigueur avec terme',
        'annulé',
        'disjoint',
        'modifié',
        'périmé',
        'substitué',
        'transféré'
    ]
    
    id = CharField(max_length=20, primary_key=True) # identifiant technique id
    version_section = ForeignKeyField(Version_section, null=True) # section parente de cet article
    nom = CharField(max_length=200) # titre de l’article
    etat_juridique = CharField(max_length=25) # état juridique de l’article au moment de la livraison
    numero = CharField(max_length=200) # numéro de l’article (e.g. L321-3-1)
    vigueur_debut = DateField() # date d’entrée en vigueur de cette version d’article
    vigueur_fin = DateField(null=True) # date de fin de vigueur de cette version d’article
    condensat = CharField(max_length=5, null=True) # condensat tronqué du texte de l’article
    texte = ForeignKeyField(Texte) # texte auquel est rattachée cette version d’article


# Classe représentant une livraison d’un texte

class Livraison_texte(BaseModel):
    
    #id = IntegerField(primary_key=True) # identifiant non-significatif
    livraison = ForeignKeyField(Livraison) # livraison mise en correspondance
    version_texte = ForeignKeyField(Version_texte) # version de texte mise en correspondance
    texte = ForeignKeyField(Texte) # texte mis en correspondance


# Classe représentant une liste de sections rattachée à une version de texte

class Liste_sections(BaseModel):
    
    #id = IntegerField(primary_key=True) # identifiant non-significatif
    version_section = ForeignKeyField(Version_section) # version de section mise en correspondance
    version_texte = ForeignKeyField(Version_texte) # version de texte mise en correspondance


# Classe représentant une liste d’articles rattachée à une version de texte

class Liste_articles(BaseModel):
    
    #id = IntegerField(primary_key=True) # identifiant non-significatif
    version_article = ForeignKeyField(Version_article) # version de section mise en correspondance
    version_texte = ForeignKeyField(Version_texte) # version de texte mise en correspondance


# Initialisation de la base de données
# 
# 
def initialisation_bdd(nom='archeo-lex.sqlite', cache='cache', effacer=False):
    
    # Suppression le cas échéant
    if effacer and os.path.exists(os.path.join(cache, 'sql', nom)):
        os.remove(os.path.join(cache, 'sql', nom))
    
    # Connexion à la base de données
    path(os.path.join(cache, 'sql')).mkdir_p()
    database = SqliteDatabase(os.path.join(cache, 'sql', nom))
    database.connect()
    database_proxy.initialize(database)
    
    # Initialisation de la base de données le cas échéant
    for modele in (Livraison, Texte, Version_texte, Version_section, Version_article, Livraison_texte, Liste_sections, Liste_articles):
        
        if not modele.table_exists():
            modele.create_table()

