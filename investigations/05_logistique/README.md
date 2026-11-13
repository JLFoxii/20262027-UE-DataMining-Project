# Développeur 5 — Logistique (INF2355M, 2026–2027)

Cet espace est **autonome** : les sept fichiers CSV d'origine restent dans
`data/logistics/` et ne doivent pas être modifiés. Le notebook constitue la
section de travail individuelle, à intégrer au rapport collectif après relecture.

## Organisation des données (méthode raw / interim / processed)

| Répertoire | Rôle |
|---|---|
| `data/logistics/` | Données officielles du professeur, **jamais modifiées** |
| `data/raw/logistics/` | Copie fidèle des 7 CSV officiels, vérifiée par SHA-256 |
| `data/interim/logistics/` | Copie de travail où **seuls les doublons exacts** ont été retirés |
| `data/interim/logistics_numeric/` | Étape intermédiaire avec des colonnes numériques ajoutées, sans modification des valeurs initiales |
| `data/processed/logistics/` | Données dédupliquées, avec colonnes numériques, dates et catégories normalisées |

Lancer la préparation depuis la racine du projet :

```bash
.venv/bin/python investigations/05_logistique/build_data.py
```

Le script peut être rejoué : il vérifie que `raw` est toujours identique aux
sources et reconstruit `interim` de façon déterministe. Le fichier
`data/interim/logistics/manifest.json` indique pour chaque CSV les lignes
avant/après, le nombre de doublons retirés et les empreintes SHA-256.
Les CSV dérivés sont ignorés par Git ; **le script et le notebook sont les
livrables reproductibles**. Ne jamais modifier `interim` à la main.

Après accord sur les formats numériques, la deuxième transformation se relance avec :

```bash
.venv/bin/python investigations/05_logistique/normalize_numeric.py
```

Ce script lit `data/interim/logistics/` et écrit dans `data/interim/logistics_numeric/` les 7 CSV, **avec toutes les
colonnes d'origine inchangées** plus les colonnes nouvelles
`<nom_de_colonne>_numeric` pour les quantités, les prix et les stocks.
Exemples : `88 case` → `88` dans `ordered_quantity_numeric` ;
`2469,48` → `2469.48` dans `unit_price_numeric`.
Les unités intégrées doivent correspondre exactement à la colonne d'unité :
sinon le programme s'arrête. `data/interim/logistics_numeric/numeric_manifest.json`
contient les comptes de conversions et les empreintes de chaque fichier.

Après accord sur les formats de dates et les variantes de casse, la troisième
transformation se relance avec :

```bash
.venv/bin/python investigations/05_logistique/normalize_dates_categories.py
```

Elle construit `data/processed/logistics/` à partir de l'étape numérique :
- ajoute `<colonne_date>_normalized` (format ISO) et
  `<colonne_date>_parse_status` sans modifier la date source ;
- laisse **vides et explicitement signalées** les trois dates `JJ/MM/AAAA`
  susceptibles d'être lues aussi comme `MM/JJ/AAAA` ; leurs deux
  interprétations figurent dans `processed_manifest.json` ;
- ajoute des colonnes `<colonne_categorie>_normalized` en minuscules
  pour les sept variables concernées par les 15 groupes de casse ;
- préserve les colonnes précédentes, les devises et les unités.

**Reproductibilité :** lancer les trois scripts dans l'ordre
`build_data.py` → `normalize_numeric.py` → `normalize_dates_categories.py`.
Le notebook suit cet ordre automatiquement. Chaque script a une source
d'entrée dédiée, ce qui évite qu'une relance de l'étape numérique efface
silencieusement les colonnes finales.

À ce stade, **aucune conversion d'unités ou de devises**, ni imputation,
suppression de valeurs manquantes, ni recherche d'anomalies n'est effectuée.
Les trois dates ambiguës restent à vérifier avant toute utilisation temporelle
et les autres problèmes éventuels seront étudiés séparément.

## Démarrage

Depuis la racine du dépôt :

```bash
~/.local/bin/uv sync --locked --inexact
~/.local/bin/uv run --no-sync jupyter lab
```

Ouvrir `investigations/05_logistique/05_logistique.ipynb` et sélectionner
le kernel `INF2355M Data Mining (Python 3.12)` ou le Python `.venv` du projet.

## Source des données

- [Consignes du dépôt](https://github.com/JLFoxii/20262027-UE-DataMining-Project)
- [Sept CSV de logistique](https://github.com/JLFoxii/20262027-UE-DataMining-Project/tree/main/data/logistics)
- [Dictionnaire officiel](https://github.com/JLFoxii/20262027-UE-DataMining-Project/blob/main/data/data_dictionary.csv)
- Recoupements prévus avec `data/public_records/registered_entities.csv`,
  `data/public_records/institutional_memos.csv` et
  `data/public_records/regulatory_case_events.csv`.

## Périmètre de la mission

1. Inventaire, qualité, granularité et clés.
2. Commandes et réceptions (joindre sur les références **et les lignes**).
3. Équations de conservation des stocks, unités et écarts.
4. Anomalies de prix, délais, quantités et autorisations.
5. Réseau logistique : installations, partenaires et flux.
6. Envois sensibles et rapprochements avec mémos / dossiers publics.
7. Rédaction avec résultats reproductibles, limites et hypothèses explicites.

**Attention :** les données sont intégralement synthétiques ; une anomalie n'est
pas une preuve de fraude. Ne pas effacer les doublons ni corriger automatiquement
les quantités hétérogènes avant d'avoir compris leur origine.

Le professeur déconseille l'IA générative : si elle est utilisée pour préparer
ou améliorer la démarche, son usage doit être documenté et justifié dans le
rapport final, selon les consignes de l'UE.
