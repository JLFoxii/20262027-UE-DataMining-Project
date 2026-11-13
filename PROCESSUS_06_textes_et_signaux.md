# Processus : Textes et signaux cardiaques

---

## 1. Objectif de la partie

Objectif global du projet (cf. `README.md`) : retrouver un **narratif / secret caché** dans des données factices, avec les méthodes de l'UE Data Mining.

Cette partie y contribue en croisant :

1. un corpus de **130 documents** (publics, mémos, notes cliniques, rapports environnementaux) ;
2. **44 enregistrements cardiaques** (métadonnées + 96 925 échantillons, 2 canaux) ;
3. les **tables CSV** servant à valider les identifiants cités dans les textes.

Lien cours → méthodes utilisées ici :

- bases / qualité des données ;
- ordonner & regrouper (K-Means, silhouette) ;
- patterns & anomalies (docs atypiques, labels signaux) ;
- graphes (cooccurrences d'entités) ;
- spatial / temporel (sites, séries cardiaques) ;
- textes (nettoyage, fréquences, TF-IDF, n-grammes).

Évaluation attendue : **méthode** claire, détaillée, reproductible (pas seulement des graphiques).

---

## 2. Périmètre des données

### 2.1 Fichiers obligatoires (cœur)

| Fichier | Dossier | Rôle | Volume |
|---|---|---|---|
| `public_and_investigative_documents.csv` | `data/public_records/` | Documents publics / enquêtes | 40 |
| `institutional_memos.csv` | `data/public_records/` | Mémos institutionnels | 30 |
| `clinical_notes.csv` | `data/health/` | Notes cliniques | 30 |
| `environmental_field_reports.csv` | `data/ecology/` | Rapports de terrain | 30 |
| `cardiac_recordings.csv` | `data/health/` | Métadonnées signaux | 44 |
| `cardiac_signal_samples.csv` | `data/health/` | Échantillons (canaux A/B) | 96 925 |
| `data_dictionary.csv` | `data/` | Dictionnaire des variables | — |

**Total textes = 130 documents.**

### 2.2 Fichiers complémentaires (croisements / validation)

| Fichier | Utilité principale |
|---|---|
| `shipments.csv` | Valider `SHP-...` |
| `purchase_order_lines.csv` | Valider `PO-...` |
| `patient_administration.csv` | Valider `PAT-...` |
| `clinical_encounters.csv` | Valider `ENC-...` |
| `monitoring_sites.csv` | Valider codes sites |
| `monitoring_device_operations.csv` | Valider `DEV-...` |
| `regulatory_case_events.csv` | Valider dossiers `REG-AAAA-NNNN` |
| `site_access_case_events.csv` | Dossiers d’accès aux sites |
| `registered_entities.csv` | Valider `REG-XXX-NNNNN` (organisations) |

### 2.3 Fichiers hors périmètre (ne pas charger pour cette partie)

- `bat_surveys.csv`, `orchard_surveys.csv`, `environmental_monthly.csv`
- `officer_filings.csv`, `public_appointments.csv`
- reste de `logistics/` hors `shipments` et `purchase_order_lines`
- optionnels seulement si enrichissement : `clinical_observations.csv`, `licensed_professionals.csv`, `licensed_facilities.csv`

---

## 3. Clés de contrôle

| Domaine | Clés |
|---|---|
| Documents | `document_id` + références citées dans le texte |
| Signaux | `recording_id`, `encounter_number`, `patient_number` |
| Règle | **toute référence extraite doit être confrontée** à la table CSV de destination |

Attention : `REG-2018-0001` (dossier réglementaire) ≠ `REG-VLN-01001` (organisation enregistrée).

---

## 4. Processus détaillé (ordre d’exécution)

### Étape 0 — Préparer l’environnement

```bash
conda create --name datamining --file requirements.txt
conda activate datamining
pip install pandas numpy matplotlib seaborn scikit-learn scipy networkx nltk
jupyter notebook 06_textes_et_signaux.ipynb
```

Le notebook doit être lancé **depuis la racine du dépôt** (là où se trouve le dossier `data/`).

### Étape 1 — Chargement et contrôles de cardinalité (Partie A)

1. Importer les bibliothèques.
2. Vérifier la présence des CSV.
3. Charger textes + signaux + tables de croisement.
4. Assert : 40 / 30 / 30 / 30 / 44 / 96925.

### Étape 2 — Corpus textuel (Mission 1)

1. Ajouter `source` (`public`, `institutional`, `clinical`, `environmental`).
2. Harmoniser `title` pour les mémos (`subject_line` → `title`).
3. Fusionner en un DataFrame `documents` (130 lignes).
4. Contrôler NA, doublons, longueurs.
5. Nettoyer → colonne `clean_text` (**garder** `text` **intact**).
6. Sauver `outputs/prepared_documents.csv`.

### Étape 3 — Thèmes (Mission 3)

1. Fréquences de mots + n-grammes (TF-IDF 2–3).
2. Matrice TF-IDF documents.
3. Choisir `K` via silhouette.
4. K-Means + termes des centres + PCA 2D.
5. Interpréter en **lisant** des titres / extraits par cluster.

### Étape 4 — Références et liens CSV (Missions 2 et 8)

1. Regex sur texte original (`SHP`, `PO`, `PAT`, `ENC`, sites, `REG`, docs, `DEV`).
2. Enrichir avec colonnes structurées (`related_*`, `patient_number`, …).
3. Valider chaque ID dans la table cible.
4. Extraire un **contexte** (±90 caractères) pour audit.
5. Sauver :
   - `outputs/extracted_references.csv`
   - `outputs/text_csv_links.csv`
   - `outputs/reference_contexts.csv`

### Étape 5 — Entités et réseau (Mission 4)

1. Entités depuis colonnes structurées (fiables).
2. Heuristique de majuscules (candidates, à prendre avec prudence).
3. Graphe NetworkX de cooccurrences + centralité.
4. Sauver `extracted_entities.csv` et `entity_centrality.csv`.

### Étape 6 — Documents particuliers (Mission 5)

1. Notes avec `superseded_document_id`.
2. Colonnes de restriction / visibilité / confidentialité.
3. Score d’anomalie = 1 − similarité cosinus moyenne (TF-IDF).
4. Sauver `atypical_documents.csv`.

### Étape 7 — Contrôle et reconstruction des signaux (Mission 6)

1. Vérifier `sample_count` déclaré vs réel.
2. Vérifier `sampling_rate_hz` / intervalle médian `time_ms`.
3. Tracer canal A / B pour des `recording_id` d’exemple.
4. Sauver `cardiac_qc.csv`.

### Étape 8 — Caractéristiques + clustering signaux (Mission 7)

1. Stats : mean, std, min, max, RMS, peak-to-peak, zero-crossings.
2. Estimation exploratoire de rythme (pics `scipy.signal.find_peaks`) — **non clinique**.
3. Standardisation + K-Means + silhouette.
4. Comparer clusters ↔ `automated_interpretation`.
5. Sauver `cardiac_features.csv`.

### Étape 9 — Signaux ↔ notes (Mission 9)

1. Jointure sur `patient_number` + `encounter_number`.
2. Détection de mots-clés liés au rythme dans les notes.
3. Table de contingence interprétation auto × présence de termes.
4. Sauver `cardiac_clinical_links.csv`.

### Étape 10 — Synthèse (Mission 10)

Pour chaque grand bloc, rédiger dans le notebook :

1. **Objectif**
2. **Méthode**
3. **Résultats** (chiffres / tableaux / figures)
4. **Interprétation**
5. **Limites**

Compléter la section « Conclusions » et les 3–5 pistes narratives **vérifiables**.

---

## 5. Organisation du notebook

```
Partie A — Environnement et données
Partie B — Volet 1 : textes
  B.1 Fusion corpus
  B.2 Qualité
  B.3 Nettoyage NLP
  B.4 Fréquences / n-grammes
  B.5 Clustering thématique
  B.6 Références + validation CSV
  B.7 Entités + cooccurrences
  B.8 Documents particuliers
Partie C — Volet 2 : signaux
  C.1 Contrôles QC
  C.2 Reconstruction
  C.3 Features + rythme exploratoire
  C.4 Clustering signaux
  C.5 Lien notes cliniques
Partie D — Synthèse / livrables / limites
```

**Point de vigilance respecté** : textes et signaux sont clairement séparés ; les croisements arrivent après des contrôles sur échantillon / tables de validation.

---

---

## 6. Limites méthodologiques à rappeler dans le rapport

1. Corpus textuel **petit** (130 docs) → clustering fragile.
2. Nettoyage / stopwords influencent TF-IDF.
3. Regex de sites `XXX-YYY` : risque de faux positifs.
4. Heuristique de noms propres ≠ vraie NER.
5. Similarité textuelle ≠ « document suspect ».
6. Features / pics cardiaques = **exploratoire**, pas un diagnostic.
7. Absence de mot-clé dans une note ≠ absence d’anomalie.
8. Données fictives → pas d’extrapolation hors projet pédagogique.

---

## 10. Transparence IA générative

L'énoncé déconseille fortement l'IA. Usage documenté dans le notebook :

- utilisée **seulement** pour clarifier quelques algorithmes (TF-IDF, K-Means, silhouette, PCA) et mieux lire les plots ;
- **pas** pour faire tout le projet à la place de l'étudiant ;
- analyses, exécution sur `data/` et interprétations faites / vérifiées par l'étudiant.

Cellule dédiée en tête de `06_textes_et_signaux.ipynb`.

---

*Fin du document processus — Développeur 6 (Nour).*
