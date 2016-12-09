Archéo Lex
==========

_Archéo Lex_ – _Pure Histoire de la Loi française_ – permet de naviguer facilement entre les différentes versions d’un texte législatif français, et vient en complément à la mise à disposition des textes offerte par [Légifrance](http://legifrance.gouv.fr).

Ainsi, chaque texte législatif (loi, code, constitution, etc.) est :

1. disponible sur un seul fichier, permettant des recherches faciles sur l’intégralité du texte,
2. dans une syntaxe minimaliste permettant de structurer le texte, et pouvant être retransformée en page HTML si besoin,
3. versionné sous Git, permettant d’utiliser toute sa puissance pour faire des comparaisons, pour rechercher dans l’historique et pour avoir une présentation lisible.


Utilisation
-----------

### Résultat et exemple d’utilisation

Pour l’exemple, le code de la propriété intellectuelle peut être consulté sur Github : <https://github.com/Seb35/CPI/blob/master/Code%20de%20la%20propriété%20intellectuelle.md>. Il est affiché ici dans sa dernière version.

Vous pouvez voir l’historique des versions du code en cliquant sur `History` dans l’en-tête du fichier, sur la droite, puis cliquer sur une des versions pour afficher les changements effectués et entrés en vigueur ce jour-là.

Sur une page affichant les différences entre versions ([exemple](https://github.com/Seb35/CPI/commit/50283dda63cef5a45a992d649b4d2ff2b1f7b546)), il est surtout affiché les modifications faites sur le texte, mais pas l’entièreté du texte. Les lignes sur fond blanc sont le contexte, identique entre une version et la suivante, et cela sert à se situer dans le texte. Il peut être ajouté plus de contexte en cliquant sur la flèche à côté des numéros de lignes. Les lignes sur fond rose correspondent au texte de l’ancienne version et celles sur fond vert correspondent au texte entrant en vigueur à partir de cette version. Pour voir l’entièreté de cette version (à cette date d’entrée en vigueur), cliquez sur `View` dans l’en-tête du fichier, à droite.


### Installation

* Installer les paquets Debian (adapter pour les autres distributions) :
  * python2.7-dev
  * libxml2-dev
  * libxslt1-dev
  * libz
  * git
* Installer les paquets Python :
  * [beautifulsoup4](https://pypi.python.org/pypi/beautifulsoup4)
  * [docopt](https://pypi.python.org/pypi/docopt)
  * [peewee](https://pypi.python.org/pypi/peewee)
  * [lxml](https://pypi.python.org/pypi/lxml)
  * [path.py](https://pypi.python.org/pypi/path.py)

L’installation de Python et de ses modules peut se faire à l’intérieur d’un environnement virtuel [`virtualenv`](https://virtualenv.readthedocs.org) afin d’imposer des versions spécifiques sans interférer avec le système par défaut. Ces paquets sont installables au moyen de [`pip`](http://pip.readthedocs.org).

La liste complète des modules utilisés est disponible au moyen de `scripts/liste-paquets.sh` (sauf lxml, optionnel mais recommandé).


### Lancement

Les données nécessaires (textes de loi et métadonnées associées) sont disponibles sur <http://rip.journal-officiel.gouv.fr/index.php/pages/juridiques> (données LEGI), à télécharger via FTP. Il faut ensuite les décompresser (attention : environ 15 Gio) et les insérer dans le sous-dossier PURE-LEGIFRANCE/cache/xml.

Le programme principal se lance en ligne de commande :

```Shell
    ./archeo-lex --textes=code-de-la-propriété-intellectuelle
```

La liste complète des paramètres s’affiche avec la commande `./archeo-lex --aide`.

Chacune des étapes peut être appelée de façon indépendante :

* `--initialisation` : initialise la base de données
* `--ranger` : parcourt les fichiers XML insère les métadonnées dans la base de données
* `--markdown` : convertit les articles en syntaxe Markdown
* `--exporter` : assemble les textes et créer les versions


Développement
-------------

Ce programme a été initialement (début août 2014) développé en 5 jours avec l’ambition d’être un prototype opérationnel et de qualité correcte. Toutefois, pour rendre ce programme et son résultat plus agréable à utiliser, les points suivants devraient être travaillés (par ordre d’importance approximatif) :

1. mise à jour des nouvelles versions des textes sans recalcul de l’entièreté de la base
2. téléchargement automatique des bases LEGI (et autres) et de leurs mises à jour incrémentales
3. intégration des modifications d’historique (orthographe, typographie, coquilles, etc.) quand les mises à jour le demandent (à étudier)
4. vérifier plus en profondeur la qualité des résultats (par exemple dans le code des assurances il y a actuellement une différence vide vers le début)
5. faire expérimenter la syntaxe Markdown et autres éléments de syntaxe à des publics non-informaticiens et réfléchir à l’améliorer (cf points 7 et 12)
6. écrire la grammaire exacte du sous-ensemble Markdown utilisé et des autres éléments de syntaxe utilisés (cf points 6 et 12)
7. documenter plus et mieux
8. ajouter des tests unitaires
9. réfléchir à une façon d’intégrer à Git les textes pré-1970 (inféfieurs à l’epoch, refusés par Git, par ex LEGITEXT000006070666)
10. travail sur les autres textes législatifs que les codes (les seuls testés actuellement), comme les Constitutions, les lois, les décrets, etc.
11. création ou adaptation d’interfaces de visualisation (cf point 16)
12. ajout de branches (orphelines) Git avec liens vers les autres textes (liens soit juste mentionnés en-dessous de l’article comme sur Légifrance, soit au sens Markdown+Git similairement à Légifrance)
13. travail sur les autres bases (KALI pour les conventions collectives, JORF pour le journal officiel -- ce dernier n’a pas de versions à ma connaissance mais demanderait juste à être transformé en Markdown)
14. mettre les dates de commit à la date d’écriture ou de publication du texte modificateur (à réfléchir) (attention : cette 2e date peut être avant, après ou identique à la date d’entrée en vigueur) pour créer des visualisations intégrant ces différences de dates
15. mise en production d’un service web qui mettrait à jour quotidiennement les dépôts Git
16. création d’un site web permettant la visualisation des modifications, proposerait des liens RSS, etc. de façon similaire à [La Fabrique de la Loi](http://www.lafabriquedelaloi.fr), à [Légifrance](http://legifrance.gouv.fr), aux sites du [Sénat](http://www.senat.fr) ou de l’[Assemblée nationale](http://www.assemblee-nationale.fr) (cf point 11)


Informations complémentaires
----------------------------

### Remerciements

* [Légifrance](http://legifrance.gouv.fr) pour l’utile présentation actuelle de l’information légale et pour le guide de légistique
* [DILA](http://www.dila.premier-ministre.gouv.fr) pour la très bonne qualité des métadonnées et pour la publication de (presque toutes les) bases de données de l’information légale
* [Regards Citoyens](http://www.regardscitoyens.org) (et d’autres ?) pour avoir poussé à la [publication des bases de données de l’information légale](http://www.regardscitoyens.org/apprenons-des-echecs-de-la-dila-episode-1-comment-faire-de-lopen-data), disponible depuis juillet 2014, la réalisation de ce programme s’en est trouvée grandement facilitée (par rapport au téléchargement de tout Légifrance) (note : au début de ce projet, je n’étais pas au courant que les bases de données n’étaient disponibles gratuitement que depuis un mois, j’arrive tout juste réellement dans le monde de l’Open Data)


### Avertissements

Les dépôts Git résultats de ce programme n’ont en aucune manière un caractère officiel et n’ont reçu aucune reconnaissance de quelque sorte que ce soit d’une instance officielle. Il n’ont d’autre portée qu’informative et d’exemple. Pour les versions d’autorité, se référer au Journal officiel de la République française.


### Licence

Ce programme est sous licence [WTFPL 2.0](http://www.wtfpl.net) avec clause de non-garantie. Voir le fichier COPYING pour les détails.


### Contact

Sébastien Beyou ([courriel](mailto:seb35wikipedia@gmail.com)) ([site](http://blog.seb35.fr))


### Liens

* [Légifrance](http://legifrance.gouv.fr), service officiel de publication de l’information légale française sur l’internet
* [La Fabrique de la Loi](http://www.lafabriquedelaloi.fr), visualisation de l’évolution des projets de lois, comportant également un dépôt Git des projets de lois
* [Direction de l’information légale et administrative (DILA)](http://www.dila.premier-ministre.gouv.fr), direction responsable de la publication du JO et assurant la diffusion de l’information légale
* [Téléchargement des bases de données d’information légale française](http://rip.journal-officiel.gouv.fr/index.php/pages/juridiques)
* [Dépôt Git d’Archéo Lex](https://github.com/Seb35/Archeo-Lex)
* [Dépôt Git d’exemple avec le Code de la propriété intellectuelle](https://github.com/Seb35/CPI)
* [Billet de blog introductif](http://blog.seb35.fr/billet/Archéo-Lex,-Pure-Histoire-de-la-Loi-française,-pour-étudier-son-évolution)

