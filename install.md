# Installation et lancement

Ce projet utilise `uv` pour créer un environnement Python isolé et identique
pour tous les membres du groupe. Il ne faut pas installer les dépendances
avec `pip` dans le Python système.

## 1. Prérequis

Il faut avoir :

- Git ;
- `uv`.

### macOS et Linux

Avec Homebrew :

```bash
brew install uv
```

Ou avec l’installateur officiel :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Fermez puis rouvrez le terminal si la commande `uv` n’est pas trouvée.

### Windows PowerShell

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Vérifiez ensuite l’installation :

```bash
uv --version
```

## 2. Récupérer le projet

Pour la première installation :

```bash
git clone git@github.com:JLFoxii/20262027-UE-DataMining-Project.git
cd 20262027-UE-DataMining-Project
```

Si le projet est déjà cloné :

```bash
cd /chemin/vers/20262027-UE-DataMining-Project
git pull
```

## 3. Installer l’environnement

Le fichier `.python-version` sélectionne Python 3.12 et `pyproject.toml`
déclare les dépendances du projet. La commande suivante crée `.venv` et
installe les versions verrouillées dans `uv.lock` :

```bash
uv python install 3.12
uv sync --locked
```

Pour vérifier que l’environnement fonctionne :

```bash
uv run python -c "import pandas, numpy, matplotlib; print('Environnement OK')"
```

Après une modification des dépendances dans `pyproject.toml`, utiliser
`uv lock` puis `uv sync`. Après un simple `git pull`, `uv sync --locked` suffit.

## 4. Lancer le notebook

Depuis la racine du projet :

```bash
uv run jupyter notebook Base_notebook_to_complete.ipynb
```

Ou avec JupyterLab :

```bash
uv run jupyter lab
```

Le notebook peut ensuite importer directement les fonctions du module
`document_analysis.py`.

## 5. Exemple d’utilisation

Dans une cellule du notebook :

```python
from document_analysis import (
    load_active_documents,
    save_output,
    set_analysis_folder,
    spearman_correlation,
)

set_analysis_folder("public_records")
documents = load_active_documents()

correlations = spearman_correlation(documents)
save_output(correlations, "correlations.csv")
```

Les dossiers d’analyse disponibles sont :

- `all` : les quatre sources textuelles ;
- `public_records` : documents publics et mémos institutionnels ;
- `health` : notes cliniques ;
- `ecology` : rapports environnementaux.

Le résultat de l’exemple sera enregistré dans :

```text
outputs/public_records/correlations.csv
```

Le dossier `logistics` n’est pas inclus dans ce sélecteur car il ne contient
pas l’un des quatre fichiers textuels étudiés dans ce module.
