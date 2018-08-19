Limitations
===========

Sont exposés ici les problèmes dans le rendu des textes, qui ne sont pas dûs à Archéo Lex per se mais à des problèmes dans les données (la [base LEGI](http://www.dila.premier-ministre.gouv.fr/repertoire-des-informations-publiques) fournie par la DILA) ou le format Git.

Outre les problèmes explicitement mentionnés ici et affectant particulièrement les résultats d’Archéo Lex, le projet [legi.py](https://github.com/Legilibre/legi.py) répertorie un certain nombre d’anomalies dans la base LEGI. Sur le site http://anomalies.legilibre.fr, ce script de détection d’anomalies tourne quotidiennement.


Dates bizarres et spéciales
---------------------------

La date du 22 février 2222 (2222-02-22) est présente dans certaines versions futures de textes. Elle signifie « date d’entrée en vigueur différée à une date non-déterminée » et signifie que l’article ou le texte entrera en vigueur à une date donnée sans que cette date ne soit pour l’instant connue. Cette date spéciale est présente dans la base LEGI et a été conservée dans Archéo Lex.

Pour des raisons informatiques dûes au format Git, les dates antérieures au 1er janvier 1970 ou postérieures au 1er janvier 2100 (notamment la date évoquée ci-dessus) peuvent apparaître comme erronées dans la « date du commit Git » dans certaines interfaces de visualisation. Ce problème est complexe à résoudre car il dépend des logiciels ou plate-formes Git qui sont utilisées pour afficher le dépôt, certaines ne gérant pas bien les dates pré-1970 et/ou post-2100. Noter que dans tous les cas, le résumé du commit avec la date écrite en français est toujours correct.

Par défaut, Archéo Lex détecte les dates pré-1970 et post-2100 et les inscrit (de façon erronée mais intentionnelle) comme le 1er janvier 1970 à 12:00 CET et 1er janvier 2099 à 12:00 CET. Deux options permettent de créer des dépôts Git en forçant les dates à prendre leurs vraies valeurs (pré-1970 et/ou post-2100), mais cela peut entraîner des incompatibilités lorsque le dépôt est traité par certains logiciels ou plate-formes Git (par exemple refus d’envoyer un dépôt vers un logiciel ou plate-forme Git, ou erreur fatale lors de l’affichage du dépôt).


Mention « (article manquant) » dans le corps de l’article
---------------------------------------------------------

Quoique rare, il manque certains contenus d’articles, la base LEGI ne contenant parfois que des métadonnées sur le nom de l’article, son état de vigueur et ses dates de vigueur. Dans ces cas, Archéo Lex inscrit « (article manquant) » en lieu et place du corps de l’article et génère un avertissement lors de la création du texte. Si la base LEGI n’a même pas de métadonnées (comportement prévu dans Archéo Lex, même si non-observé pour l’instant), le titre de l’article est « (inconnu) ».

Ce problème a été soulevé dans l’[issue 30](https://github.com/Legilibre/Archeo-Lex/issues/30). Si vous souhaitez discuter autour de ce sujet, vous pouvez y ajouter un commentaire (même si l’issue est fermée car résolue autant que faire se peut).

Un exemple (présent dans la base LEGI de juillet 2018) est l’article R425-29-1 du code de l’urbanisme, entré en vigueur le 31 octobre 2015 et sans date de fin de vigueur. On notera que l’article est présent sur [Légifrance](https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000031398648&cidTexte=LEGITEXT000006074075), ce qui permet de penser que la base LEGI fournie par la DILA diffère en partie de la base LEGI utilisée par Légifrance.


Disparition ou non-apparition d’un article à une date donnée
------------------------------------------------------------

Dans certains cas, il peut manquer purement et simplement certains articles, sans aucune mention explicite comme évoqué au paragraphe précédent, alors qu’ils auraient dû être présents. La faute peut être imputable soit à Archéo Lex (bug interne) soit à la base LEGI elle-même.

Un bug interne à Archéo Lex a été présent depuis la création d’Archéo Lex jusqu’au 27 mai 2018 et se révélait lorsque des sections étaient renommées mais que les articles contenus restaient inchangés. Ce problème est censé avoir été résolu (voir l’[issue 11](https://github.com/Legilibre/Archeo-Lex/issues/11)) mais il n’est pas exclu que d’autres cas particuliers entraînant une disparition ou non-apparition d’articles se révèlent.

Dans d’autres cas toutefois, la faute est imputable à la base LEGI elle-même, où des articles peuvent exister mais être rattaché à une mauvaise section parente, entraînant une non-apparition dudit article. C’est le cas par exemple de l’article [L132-1 du code de la propriété intellectuelle](https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000006278971&cidTexte=LEGITEXT000006069414&dateTexte=19920703) dans la version initiale du 3 juillet 1992. Cet article est erronément affecté à la sous-section 1 de la section 1 du chapitre L132 introduite le 1er décembre 2014 au lieu d’être affecté à la section 1 du chapitre L132 introduit le 3 juillet 1992. Ce problème de rattachement fait que cet article semble avoir été introduit le 1er décembre 2014 alors qu’il existait bien avant cette date. Le problème est actuellement (juillet 2018) également présent sur Légifrance.


Cas des articles morts-nés
--------------------------

Les articles morts-nés (appellation officielle dans la base LEGI) sont ceux qui, après avoir été introduit avec une date d’entrée en vigueur différée, sont abrogés avant ladite date d’entrée en vigueur : ils ont donc une date de fin de vigueur antérieure à leur date d’entrée en vigueur (la date initialement prévue). Dans les versions d’Archéo Lex antérieures au 12 août 2018, et lorsque les seuls articles modifiés d’une version étaient des articles morts-nés, un avertissement était affiché lors de l’exécution d’Archéo Lex ; cet avertissement n’est plus affiché du fait que les articles morts-nés ne sont plus comptabilisés comme « date où il y a une modification du texte ».

Les articles morts-nés ne sont donc jamais visibles dans les textes issus d’Archéo Lex, dans le sens qu’ils n’ont jamais été en vigueur. Quoique ce comportement est probablement le plus utile pour la majorité des utilisateurs, il est possible que certains utilisateurs soient intéressés pour voir s’afficher d’une façon ou d’une autre les articles morts-nés, je pense par exemple à des chercheurs archéologues de la loi. Dans ce cas, il est demandé de créer une demande de fonctionnalité, où serait discuté la meilleure façon de rendre visibles ces articles morts-nés.
