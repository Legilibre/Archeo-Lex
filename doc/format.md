Format Archéo Lex
=================

Archéo Lex a pour but de fournir une version à la fois épurée, puissante et stable des textes de lois français. Cela se traduit par un texte en Markdown le plus interopérable possible et un versionnement au format Git.

Le format décrit dans ce document tend à fixer le plus précisément possible un format de données permettant d’encoder les textes de lois français et leur historique au moyen des deux standards Markdown et Git.

L’esprit qui préside au format décrit ci-après est d’être le plus interopérable possible afin de s’afficher et d’être utilisé avec le moins de freins possibles, sauf lorsqu’il est absolument nécessaire de s’affranchir des standards pour conserver le sens et/ou la cohérence de l’édifice entier.

Le programme Archéo Lex permet de générer plusieurs formats. Le format décrit dans ce document est le format par défaut : texte entier en syntaxe Markdown, dans un seul fichier, enregistré dans Git.


Markdown
--------

Le texte de chaque version – à une date d’entrée en vigueur donnée – est structuré selon le format Markdown, avec une légère variation.

Voici le détail des éléments de syntaxe standards :

- Les paragraphes sont séparés entre eux par une ligne vide et un paragraphe ne comporte aucun retour à la ligne (informatiquement parlant, la largeur des écrans entraîne de facto un retour à la ligne visuel par les logiciels d’affichage),
- Les listes à puces sont précédées d’une ligne vide et chaque point est sur une ligne débutant par un tiret et une espace : "- ",
- Les titres sont sur une ligne indépendante débutant par un certain nombre de croisillons "#" correspondant à leur niveau hiérarchique.

Les éléments de syntaxe astandards sont :

- Les listes numérotées sont traitées comme des paragraphes séparés afin de conserver l’exacte numérotation (y compris par exemple avec des "bis"),
- Le niveau des titres n’est pas limité à 6 contrairement au Markdown standard (il peut atteindre 11),
- Les tableaux sont écrits en HTML dont chaque ligne de texte est soit une balise ouvrante ou fermante \<table\>, \<\/table\>, \<tr\>, \<\/tr\>, soit une cellule commançant par \<td\> et se terminant par \<\/td\> ; exceptionnellement, lorsque le contenu de la cellule exige plusieurs lignes, celui-ci sera toutefois inscrit sur plusieurs ligne de texte.

### Correspondance légistique avec le texte brut

Le texte brut est façonné de façon à faciliter les interactions avec les notions légistiques.

Les articles voient leur titre comme un titre Markdown tel que décrit ci-dessus et commencent toujours par la chaîne de caractère "Article ". Il est ainsi possible d’extraire automatiquement le sommaire d’un texte.

Sauf le cas particulier des tableaux, les alinéas peuvent se décompter en comptant les retours à la ligne et en ignorant les lignes vides, pour leur méthode de décompte générale depuis 2001 (et version Parlement pour pré-2001). La méthode de décompte Conseil d’État pré-2001 est moins directe mais peut également se transcrire relativement facilement en un algorithme. Voir la circulaire du 20 octobre 2000 (NOR PRMX0004462C) pour les différentes méthodes de décompte.


Git
---

Le versionnement est assuré par le logiciel Git.

De part sa conception, les numéros de versions changent dès qu’un seul caractère du texte change quelque part dans l’historique passé ou présent du texte. Il est ainsi d’une nécessité absolue, pour préserver la stabilité voir la pérennité des numéros de versions Git, que le dialecte exact des textes au format Markdown soit stable. En conséquence, le changement du numéro de version à une date d’entrée en vigueur donnée sera ainsi le signe d’une modification éditoriale dans cette version ou dans une version passée.

Deux sortes de dépôts Git peuvent être créés :

- un dépôt Git comportant un seul texte de loi,
- un dépôt Git comportant tout le corpus des textes de loi.

### Historique d’un texte de loi

Chaque version d’un texte enregistré dans Git est une nouvelle version du texte, entrant en vigueur à la date indiquée dans le commit Git. Toute version enregistrée dans Git comporte obligatoirement une modification du texte par rapport à la version précédente.

Chaque version comporte un seul fichier contenant le texte Markdown tel que décrit ci-avant. Le nom de ce fichier commence par une lettre minuscule, a l’extension ".md", et dont les espaces sont remplacés par des tirets bas "\_", nommé avec la convention suivante :

- Codes juridiques français : nom du code, les diacritiques et les majuscules relatives aux noms propres sont conservées, les apostrophes sont des apostrophes droites "'", par exemple "code\_de\_l'Office\_national\_interprofessionnel\_du\_blé.md",
- Textes ayant une nature et un numéro : nature du texte, suivi d’une espace, suivi du numéro du texte, par exemple "loi\_78-17.md" ou "loi\_organique\_2001-692.md",
- Textes non-numérotés ayant un article dans la Wikipédia en français : le titre canonique de l’article Wikipédia en français est utilisé, par exemple "ordonnance\_de\_Villers-Cotterêts.md".

Les métadonnées d’un commit sont fixés ainsi :

- Le message du commit est : "Version consolidée au [date]", la date étant écrite en français sous la forme "\[jour\] \[mois\] \[année\]", le jour comportant un ou deux chiffres avec le cas particulier du "1" qui est noté "1er", le mois est écrit en toutes lettres et l’année comportant quatre chiffres, le calendrier utilisé est le calendrier alors en vigueur à l’époque donnée (grégorien, républicain, julien), par exemple "15 mars 2001", "1er janvier 2004", "15 vendémiaire an II",
- Le nom de l’auteur (author) et de l’expéditeur (committer) sont fixés à "Législateur", l’adresse email est fixée à vide "", la combinaison des deux donnant "Législateur <>" dans le format brut (raw) d’un commit Git,
- La date du commit (AuthorDate) et de l’expédition (CommitDate) sont fixées à minuit au jour de l’entrée en vigueur de la version du texte, dans le fuseau horaire légal à l’époque correspondante.

Dans les époques récentes, le fuseau horaire alterne donc entre +0100 (CET) et +0200 (CEST). Toutefois, il est fixé par convention à +0009 Local Mean Time (LMT) pour la période avant l’apparition des fuseaux horaires. Le fuseau horaire de référence est ultimement donné par la base de données de référence tzdata.

La date étant indiqué au format Epoch dans Git (nombre de secondes depuis le 1er janvier 1970 à 00:00:00 UTC, hors secondes intercalaires), il est nécessaire d’utiliser un nombre négatif pour toute date précédent le 2 janvier 1970 (le 1er janvier 1970 étant -3600 en France étant donné le fuseau horaire CET). Quoique le format Git n’est pas défini avant l’Epoch, la forme standard des dépôts Git créés par Archéo Lex est de forcer à la date réelle, donc comportant un nombre négatif de secondes pour la période précédent l’Epoch.

Il faut noter que, début 2019, l’exécutable officiel Git peut lire les tels dépôts mais affiche la date du 1er janvier 1970 pour toute date avant l’Epoch, et les plate-formes GitHub et Gitlab refusent de charger de tels dépôts Git. Le programme Archéo Lex permet de créer des dépôts compatibles avec des champs date erronés, mais cette forme de dépôt n’est pas standard au sens du présent document.

Les versions en vigueur future peuvent également faire l’objet de commits sans distinction des commits en vigueur passée. Lorsqu’une entrée en vigueur future n’a pas de date précise au moment de la consolidation, il est attribué la date spéciale "22 février 2022" (minuit, CET) et le message de commit "Version consolidée à une date future indéterminée", par cohérence avec la pratique de Légifrance.

En cas de différence entre la date enregistrée dans les champs AuthorDate et CommitDate et la date écrite dans le message du commit, la date faisant autorité est celle du message de commit.

### Organisation d’un dépôt Git comportant un seul texte de loi

Un dépôt Git comportant un seul texte de loi peut comporter une ou deux branches au sens Git parmi les trois noms de branches possibles, en fonction de l’état de vigueur du texte :

- branche "texte" (référence refs/heads/texte) pointant sur la dernière version en vigueur du texte, lorsque le texte est en vigueur au moment du calcul du dépôt Git,
- branche "texte-futur" (référence refs/heads/texte-futur) pointant sur la dernière version en vigueur future du texte, soit lorsque le texte est en vigueur et comporte des versions en vigueur future soit lorsque le texte n’est pas encore entré en vigueur au moment du calcul du dépôt Git,
- branche "texte-abrogé" (référence refs/heads/texte-abrogé) pointant sur une version vide à la date de l’abrogation et comportant le message de commit "Texte abrogé au [date]".

Ainsi, les quatre configurations suivantes de branches sont possibles :

- une branche "texte" : texte en vigueur sans aucune version en vigueur future,
- deux branches "texte" et "texte-futur" : texte en vigueur avec une ou plusieurs versions en vigueur future,
- une branche "texte-futur" : texte qui n’est pas encore en vigueur mais dont une ou plusieurs versions en vigueur future sont déjà prêtes,
- une branche "texte-abrogé" : texte abrogé.

Un texte abrogé se traduit par une version vide datée du jour de l’abrogation et comportant le message de commit "Texte abrogé au [date]". Lorsque l’abrogation est prévue à une date future, un tel commit peut être contenu dans la branche "texte-futur".

### Corpus des textes de loi

L’ensemble (ou une partie) des textes de loi français peut être rassemblée dans un unique dépôt Git.

Chaque texte est stocké dans une branche orpheline du dépôt Git, accessible via une ou deux références correspond aux branches mentionnées ci-avant. Les références d’un texte suivent la convention de nommage suivante :

  refs/[nature]/[identifiant]/[branche]

avec :

- [nature] : nature du texte ("code", "loi", "loi organique"…)
- [identifiant] : identique au nom du fichier, sans l’extension .md
- [branche] : nom de la branche, parmi : "texte", "texte-futur", "texte-abrogé"


Révision de ce document
-----------------------

Ce document a été créé le 9 mars 2019 dans un stade de proposition de standard. Il suivra un versionnement sémantique à partir du 1er juillet 2019 où sera créée la version 1.0.0.

Version 0.1.0
