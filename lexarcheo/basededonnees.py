# -*- coding: utf-8 -*-
# 
# Archéo Lex – Pure Histoire de la Loi française
# – crée un dépôt Git des lois françaises écrites en syntaxe Markdown
# – ce module gère la structure de la base de données
# 
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# the LICENSE file for more details.

# Imports
from __future__ import (unicode_literals, absolute_import, division, print_function)
import os
from path import path
from peewee import (Model, SqliteDatabase, BlobField, BooleanField, CharField, DateField, ForeignKeyField, IntegerField)

# Initialisation de la base de données
bd = SqliteDatabase('cache/autre/archeo-lex.sqlite')
bd.connect()


## Définition des classes représentant les articles, textes et leur versionnement

# Classe représentant un texte

class Texte(Model):
    
    class Meta:
        
        database = bd
        enum_natures = [
            'constitution',
            'code',
            'loi',
            'loi constitutionnelle',
            'ordonnance',
            'décret',
            'arrêté',
            'décret-loi'
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
    
    cid = CharField(max_length=20, primary_key=True)
    nor = CharField(max_length=20)
    nature = CharField(max_length=20, choices=enum_natures)
    date_texte = DateField(null=True)
    date_publi = DateField(null=True)


# Classe représentant une version d’un texte
# Noter qu’une version d’un texte peut
# - « faire autorité » (base==NULL), version correspondant
#   à un champ META_TEXTE_VERION de Légifrance
# - « ne pas faire autorité » (base!=NULL), l’unique version d’autorité
#   liée est indiquée dans le champ base, ce type de version correspond
#   à un changement d’au moins un des articles ou de la section du texte

class Version_texte(Model):
    
    class Meta:
        
        database = bd
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
    
    texte = ForeignKeyField(Texte, related_name='versions_texte')
    titre = CharField(max_length=200)
    titre_long = CharField(max_length=200)
    etat_juridique = CharField(max_length=25)
    debut = DateField(null=True)
    fin = DateField(null=True)
    base = ForeignKeyField('self', null=True)


# Classe représentant l’arborescence des textes, en particulier les codes

class Section(Model):
    
    class Meta:
        
        database = bd
    
    cid = CharField(max_length=20, primary_key=True)
    cid_parent = ForeignKeyField('self', related_name='sections', null=True)
    niveau = IntegerField()
    texte = ForeignKeyField(Texte, related_name='sections')


# Classe représentant une version d’une section

class Version_section(Model):
    
    class Meta:
        
        database = bd
    
    cid = ForeignKeyField(Section, related_name='versions_section')
    id = CharField(max_length=20, primary_key=True)
    id_parent = ForeignKeyField('self', null=True)
    nom = CharField(max_length=200)
    etat_juridique = CharField(max_length=25)
    niveau = IntegerField()
    numero = IntegerField()
    debut = DateField()
    fin = DateField(null=True)
    texte = ForeignKeyField(Texte)
    version_texte = ForeignKeyField(Version_texte, null=True)


# Classe représentant une version d’un article

class Article(Model):
    
    class Meta:
        
        database = bd
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
    
    id = CharField(max_length=20, primary_key=True)
    nom = CharField(max_length=200)
    etat_juridique = CharField(max_length=25)
    num = CharField(max_length=200)
    debut = DateField()
    fin = DateField(null=True)
    texte = ForeignKeyField(Texte)
    version_section = ForeignKeyField(Version_section)
    version_texte = ForeignKeyField(Version_texte)
    #cree_par = ForeignKeyField(Version_texte, related_name='crees_par')
    #article_predecesseur = ForeignKeyField('self', null=True)


def initialisation_bdd(nom='archeo-lex.sqlite', cache='cache', effacer=False):
    
    # TODO ceci est inopérant et donc on ne peut pas choisir le nom de la BDD
    #path(os.path.join(cache, 'autre')).mkdir_p()
    #bd = SqliteDatabase(os.path.join(cache, 'autre', nom))
    #bd.connect()
    
    for modele in (Section, Texte, Version_texte, Version_section, Article):
        
        if effacer:
            modele.drop_table(fail_silently=True)
        
        if not modele.table_exists():
            modele.create_table()

