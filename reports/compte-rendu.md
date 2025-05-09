# Fouille de Texte - M1 TAL 2024/2025
# [Classification de texte par date](https://github.com/16arpi/fouille-texte-2025/)

## César Pichon ([@16arpi](https://github.com/16arpi))
## Damien Biguet ([@NiLuJe](https://github.com/NiLuJe))

TODO: ToC

----

# Objectifs

L'objectif de ce projet est de classifier des documents textuels en français par date, plus spécifiquement dans des intervalles de 50 ans. L'hypothèse étant que l'évolution de la langue française au cours du temps, tant au niveau lexical que grammatical devrait rendre possible une modélisation de ces évolutions par les algorithmes de classification étudiés en cours.

# Données & Ressources

En quête de données adaptées (du texte en français, écrit à des périodes s'étalant le plus loin possible dans l'histoire), nous avons regardé du côté de [Gallica](https://gallica.bnf.fr/accueil/fr/html/accueil-fr), [Projet Gutenberg](https://gutenberg.org/), ainsi que [Internet Archive](https://archive.org/), avant finalement de nous décider à exploiter uniquement [Wikisource FR](https://fr.wikisource.org/wiki/Wikisource:Accueil), principalement car l'intégralité du contenu est, entre autres, classé par date de publication, rendant l'exploitation de cette information idéale pour notre projet.

De plus, la fondation Wikimedia met à disposition [des copies complètes des données](https://dumps.wikimedia.org/) de ses divers wiki, ce qui nous paraissait relativement pratique: pas besoin de gérer un *scrapping* web plus ou moins hasardeux. On verra plus tard que cette approche se révélera en fait être à double tranchants (voire... à triple tranchants...).

Un autre intérêt de Wikisource est l'aspect légal non-ambigu: tout le contenu est libre, sous licence [CC-BY-SA](https://creativecommons.org/licenses/by-sa/4.0/deed.fr).

## Exploitation du dump wikisource

Nous voilà donc parti pour exploiter le *dump* du [20 mars 2025](https://dumps.wikimedia.org/frwikisource/20250320/) de Wikisource FR (spécifiquement, le fichier *frwikisource-20250320-pages-meta-current.xml.bz2*).  
Ces fichiers sont donc au format XML (selon un schéma [bien définit](https://meta.wikimedia.org/wiki/Data_dumps/Dump_format)) et compressé en BZ2. Au hasard des recherches sur les outils disponibles pour traiter ces fichiers, nous tombons sur le projet [xmltodict](https://github.com/martinblech/xmltodict): un module Python qui convertit une arborescence XML en objets natifs Python. La présentation du projet fait ressortir deux points importants pour notre utilisation: l'utilisation d'un parser XML de type SAX, donc qui ne va pas avoir besoin de charger l'intégralité du fichier en mémoire (un point relativement important vu la taille du dump: 2.3GB *compressé*); et le fait qu'il ait visiblement été testé sur des dumps Wikimedia.

On implémente cette passe de conversion [via une simple pipeline shell](https://github.com/16arpi/fouille-texte-2025/blob/348b7b87b2017e96a2190ef58de05eaa2b94f803/data/make_dataset.sh#L39-L43), et l'on stocke le résultat dans un fichier compressé par [zstandard](https://github.com/facebook/zstd), pour ses performances idéales (compression très correcte, et *excellentes* performances en décompression).  
Et c'est là que l'on va pour la première fois se confronter au challenge de gérer une telle quantité de données: alors que la partie parser XML travaille en *streaming*, la représentation en objets Python, elle, beaucoup moins, puisque les données s'accumulent petit à petit... Bref, on se retrouve en fin de traitement avec un joli pic d'occupation mémoire à 24GB!

## Exploration & Extraction des données



# Méthodologie

# Expériences

# Résultats



