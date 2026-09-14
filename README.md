# Année 2026-2027 - M2IA/M2DS - UE Data Mining - Projet

Sur ce repository, vous pourrez trouver l’ensemble des éléments
nécessaire au projet de groupe de l’UE Data Mining pour l’année 2026-2027.

Votre objectif est de mettre en évidence le narratif caché à l’intérieur
de ces données à l’aide des notions et méthodes vues au fur et
à mesure de l’UE Data Mining.

/!\ Ce narratif est entièrement fictif. Il a été créé dans un objectif pédagogique et ne reflète aucunement la réalité /!\

Pour ce faire, vous travaillerez en groupe en débattant et
en vous répartissant les tâches à faire.

Le rendu attendu est un rapport, sous la forme d’un notebook jupyter,
qui détaillera vos réflexions, les méthodes et vos conclusions.

Pour cela, le fichier `Base_notebook_to_complete.ipynb` est mis à votre disposition (vous pouvez changer le nom si vous le souhaitez).

Pensez à bien y préciser:

* Le nom de votre groupe
* La liste des membres

Vous serez avant tout évalué sur votre méthode, donc soyez précis, détaillé
et rigoureux dans vos descriptions.

/!\ L’usage de l’IA Générative est fortement déconseillé (ce sont vos cerveaux que l’on souhaite entrainer ici).
Si vous souhaitez tout de même l’utiliser, cela doit être justifié et documenté dans votre rapport /!\

## Jeux de données

Dans le dossier `data/`, vous trouverez les ensembles des jeux de données suivants:

- `data/public_records/` — jeux de données issus d’institutions administratives publiques,
- `data/health/` — jeux de données médicales issus de cliniques et d’hôpitaux,
- `data/ecology/` — jeux de données issus de recherches environnementales,
- `data/logistics/` — jeux de données issus de groupes et d’entreprises privées.

Le fichier `data/data_dictionary.csv` détaille les caractéristiques des variables présentes dans chaque jeu de données.

/!\ Ces jeux de données sont entièrement synthétiques et ont été créé dans un but pédogagique.
Ils ne représentent pas des informations factuelles à propos de personnes réelles,
d’organisations réelles, de gouvernnements réels ou localisations réelles.
Toute ressemblance avec des personnes réelles, physiques ou morales, est totalement involontaire et fortuite. /!\ 
 
## Pour bien commencer

Pour une installation multiplateforme reproductible avec `uv`, consultez le
fichier [`install.md`](install.md).

1. Faites un `fork` de ce repository vers un noveau repository pour votre groupe.
2. Clonez le repository de votre groupe sur votre machine.
3. Installez les dépendances avec `uv sync --locked` (voir [install.md](install.md)).
4. Lancez le notebook avec `uv run jupyter notebook Base_notebook_to_complete.ipynb`.
5. Travaillez en groupe et complétez le notebook.

Le fichier `requirements.txt` est un ancien export Conda spécifique à Windows.
Pour une installation multiplateforme, utilisez `pyproject.toml` et `uv.lock`.

## Rendu

Le rendu pourra se faire via:

* une `pull-request`, 
* en m’envoyant une archive .zip contenant votre travail à `antoine.richard@chu-lyon.fr`.
