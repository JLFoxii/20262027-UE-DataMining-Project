# Reproduction du rapport collectif sans code visible

Le rendu à remettre est **`Rapport_collectif_Data_Mining_M2DS_2026_2027.ipynb`**, situé à la racine du dépôt. C'est un notebook Jupyter contenant uniquement du **Markdown**, des tableaux et des graphiques PNG intégrés directement dans le notebook. Il est lisible sans exécuter de Python.

Le calcul des résultats et la construction des figures sont séparés de la lecture :

- `scripts/calculs_rapport_collectif.py` : les **19 blocs de calculs** qui lisent les données disponibles dans `data/` et le tableau écologique versionné `exports/ecologie/tableaux/comparaison_acces.csv` ; aucun CSV source n'est modifié.
- `scripts/generer_rapport_sans_code.py` : exécute ces blocs dans l'environnement du projet puis remplace **uniquement** les tableaux et figures du notebook final. Les paragraphes Markdown, les titres et les autres modifications rédactionnelles sont préservés.

## Reproduire les résultats

Depuis la racine du dépôt :

```bash
uv sync --locked
uv run python scripts/generer_rapport_sans_code.py --check
uv run python scripts/generer_rapport_sans_code.py --reexecute
```

La commande `--check` valide le notebook existant **sans le modifier**. La commande `--reexecute` recalcule les tableaux et graphiques, puis les intègre au notebook (sans y ajouter de code). L'utilitaire n'a **aucune dépendance aux versions de brouillon** du rapport, qui ne font pas partie du dépôt.

Pour les méthodes détaillées des six études, consulter leurs notebooks individuels (dont `investigations/05_logistique/05_logistique.ipynb`). Ce rapport synthétise leurs résultats ; il ne remplace pas les analyses individuelles. Les informations portant sur l'utilisation de l'IA et les limites scientifiques figurent dans le rapport et doivent rester fidèles aux travaux réellement réalisés.
