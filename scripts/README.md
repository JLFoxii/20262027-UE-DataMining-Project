# Reproduction du rapport collectif sans code visible

Le rendu à remettre est **`Rapport_collectif_Data_Mining_M2DS_2026_2027.ipynb`**, situé à la racine du dépôt. C'est un notebook Jupyter contenant uniquement du **Markdown**, des tableaux et des graphiques PNG intégrés directement dans le notebook. Il est lisible sans exécuter de Python.

Le calcul des résultats et la construction des figures sont séparés de la lecture :

- `scripts/calculs_rapport_collectif.py` : les **19 blocs de calculs** qui lisent les données disponibles dans `data/` et le tableau écologique versionné `exports/ecologie/tableaux/comparaison_acces.csv` ; aucun CSV source n'est modifié.
- `scripts/generer_rapport_sans_code.py` : exécute ces blocs dans l'environnement du projet puis actualise **uniquement les sorties de calcul non retouchées par le groupe**. Les paragraphes, tableaux remaniés, images ajoutées et autres corrections éditoriales du groupe sont préservés.

## Reproduire les résultats

Depuis la racine du dépôt :

```bash
uv sync --locked
uv run python scripts/generer_rapport_sans_code.py --check
uv run python scripts/generer_rapport_sans_code.py --reexecute
```

La commande `--check` valide le notebook existant **sans le modifier** (46 cellules Markdown, **8 figures** et 13 tableaux). La commande `--reexecute` relance tous les calculs, mais **ne remplace pas les huit sorties déjà corrigées ou enrichies manuellement par le groupe**, notamment la figure supplémentaire des flux logistiques. Les autres sorties sont réactualisées sans ajouter de code au notebook. Les calculs reproduisent les résultats d'origine ; les annotations et enrichissements ajoutés par le groupe restent la version faisant foi. L'utilitaire n'a **aucune dépendance aux anciennes versions de brouillon** du rapport, qui ne font pas partie du dépôt.

Pour les méthodes détaillées des six études, consulter leurs notebooks individuels (dont `investigations/05_logistique/05_logistique.ipynb`). Ce rapport synthétise leurs résultats ; il ne remplace pas les analyses individuelles. Les informations portant sur l'utilisation de l'IA et les limites scientifiques figurent dans le rapport et doivent rester fidèles aux travaux réellement réalisés.
