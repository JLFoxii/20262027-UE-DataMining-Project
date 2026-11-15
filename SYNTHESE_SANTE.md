# Partie santé — éléments à intégrer au rapport commun

**Auteur :** Irfat Fejzullahu.  
**Source :** [03_sante.ipynb](03_sante.ipynb), en particulier les §5, §7 et §8.  
**Périmètre :** données synthétiques du projet pédagogique.

## Résultats essentiels

| Résultat | Valeur | Méthode et portée |
|---|---|---|
| Données après dédoublonnage | 240 patients, 1 067 consultations, 17 734 observations, 310 procédures | Six copies exactes retirées ; les valeurs manquantes et les mesures signalées restent conservées. |
| Comparaison des pouls | 1 017 paires chez 240 patients ; écart moyen apical − périphérique de 3,96 bpm | Même patient et consultation, valeurs présentes en bpm ; mesures espacées de 30 secondes. |
| Écarts de pouls repérés | 50 paires chez 18 patients | Bornes exploratoires Q1 − 1,5 × IQR et Q3 + 1,5 × IQR : −17,15 et 23,25 bpm. Ces bornes ne sont pas des seuils médicaux. |
| Profils exploratoires | Trois groupes de 112, 105 et 23 patients ; silhouette de 0,308 | K-means sur l'âge, l'écart de pouls médian et le débit estimé médian, après standardisation ; séparation modérée. |
| Actes MRP-42 | 50 actes chez 28 patients | Huit patients ont reçu plusieurs actes, pour 30 actes au total ; les vingt autres bénéficiaires ont un acte chacun. |
| Correspondances publiques | Neuf paires classées probables | Critères de naissance, région, profession et chronologie ; aucune identité confirmée par un identifiant personnel commun. |
| Enregistrements | 44 acquisitions, 96 925 lignes d'échantillons, 42 patients et 42 consultations | Contrôles des liens, des effectifs et des grilles temporelles cohérents. |
| Points de qualité | 25 décalages entre valeur, intervalle fourni et interprétation ; huit notes antérieures à leur consultation | Cas conservés et signalés ; aucun champ arbitrairement corrigé. |

## Détail des bénéficiaires répétés de MRP-42

| Patient | Nombre d'actes MRP-42 |
|---|---:|
| PAT-31221 | 5 |
| PAT-31044 | 4 |
| PAT-31074 | 4 |
| PAT-31119 | 4 |
| PAT-31174 | 4 |
| PAT-31099 | 3 |
| PAT-31142 | 3 |
| PAT-31183 | 3 |

Ces nombres décrivent les actes enregistrés. Les durées de suivi diffèrent entre patients. Cette analyse ne mesure ni l'efficacité de MRP-42 ni un éventuel gain de longévité.

## Deux acquisitions de PAT-31065

Les deux acquisitions sont rattachées à `ENC-000038`. L'autocorrélation donne les périodicités suivantes :

| Enregistrement | Modèle d'appareil | Canal A, cycles/min | Canal B, cycles/min |
|---|---|---:|---:|
| CRD-410038 | Asterion CV-3 | 66,37 | 98,68 |
| CRD-410005 | HelixCard Duo | 66,67 | 100,00 |

Ces motifs sont proches des pouls de la consultation : **66,8 bpm périphérique** et **99,2 bpm apical**. L'heure exacte des acquisitions et les informations de calibration manquent : leur simultanéité avec les mesures n'est pas certifiée.

`CLN-510027` décrit des sources de contraction partiellement indépendantes et envisage plusieurs explications. Cela reste une affirmation documentaire à confronter aux examens. Les deux périodicités ne prouvent pas la présence de deux cœurs. Dans `CLN-510126`, pour un autre patient, la formulation « dual cardiac structures » est rejetée après repositionnement : le contexte des mots doit être conservé.

## Attribution documentaire à Elias Voss

`CLN-510025` attribue à `PAT-31065` l'identité d'Elias Voss. La fiche patient indique une naissance le **9 octobre 1975**, tandis que le mandat `FLG-000004` donne **1961** pour Elias Voss.

**Formulation à reprendre :** « L'attribution documentaire de PAT-31065 à Elias Voss n'est pas reproduite par nos critères de naissance. Elle reste une hypothèse à vérifier et n'est pas incluse dans les neuf correspondances probables. »

Cette divergence ne suffit pas à réfuter définitivement une identité. Elle ne doit pas non plus être effacée par une explication narrative non vérifiée.

## Proposition de paragraphe pour le rapport

L'analyse de santé met en évidence des écarts de pouls répétés et des interventions spécialisées reçues plusieurs fois. Sur 1 017 paires comparables, la règle exploratoire des quartiles repère 50 écarts chez 18 patients. MRP-42 représente 50 actes chez 28 patients, dont huit bénéficiaires répétés. Pour PAT-31065, deux acquisitions sur des modèles d'appareil différents reproduisent deux périodicités cohérentes avec les mesures apicale et périphérique de la consultation. Ces observations ne déterminent ni une anatomie ni l'efficacité des interventions. Neuf rapprochements avec des personnalités publiques sont classés probables selon les critères retenus ; l'attribution à Elias Voss reste distincte, documentaire et non reproduite par les années de naissance. Ces résultats contribuent au récit commun lorsqu'ils sont confrontés aux registres, aux flux et aux documents, en conservant les contradictions de dates et d'identité.

## Exports et reproduction

Depuis la racine du dépôt :

```bash
uv sync --locked
uv run jupyter nbconvert --to notebook --execute --inplace 03_sante.ipynb
```

Cette exécution régénère les figures et CSV dans `outputs/sante/`, sans dépendre des résultats d'un autre notebook. Les exports utiles pour le rapport sont :

- `resume_sante.csv` : tableau de synthèse calculé ;
- `comparaison_pouls.csv` et `ecarts_pouls_a_examiner.csv` : paires comparables et écarts repérés ;
- `mrp42_par_patient.csv` : nombres et périodes des actes par bénéficiaire ;
- `periodes_signaux_exemple.csv` : périodicités avec modèles d'appareil et références patient/consultation ;
- `correspondances_probables.csv` : neuf rapprochements à confirmer ;
- `incoherences_interpretation.csv` et `notes_dates_a_verifier.csv` : points de qualité à conserver dans l'interprétation.

Le dossier `outputs/` est ignoré par Git ; le notebook et les CSV sources suffisent à régénérer ces fichiers.

## Assistance IA

Une IA générative a été utilisée pour aider à la syntaxe Python, à la vérification des résultats, à la formulation des interprétations et à la rédaction de la documentation.
