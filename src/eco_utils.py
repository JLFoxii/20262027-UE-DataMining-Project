"""
functions.py
============

Bibliothèque de fonctions utilitaires pour le prétraitement
et l'exploration des données du projet Data Mining.

Fonctionnalités
---------------
1. Normalisation des valeurs numériques et des unités.
2. Identification, normalisation et conversion des dates.
3. Détection des valeurs invalides et incohérentes.
4. Exploration des valeurs manquantes et des doublons.
5. Normalisation des variables textuelles et catégorielles.
6. Détection des valeurs aberrantes et des catégories rares.

Conventions
-----------
- Les fonctions de normalisation modifient directement le DataFrame.
- Les fonctions d'exploration retournent les résultats sans modifier les données.
- Les valeurs manquantes sont généralement conservées ou ignorées.
- Les anomalies détectées ne sont jamais supprimées automatiquement.

Dépendances
-----------
pandas >= 2.0
Python 3.x
"""

import re

import pandas as pd


# ========================================================================
# Nettoyage numérique et unités
# ========================================================================


def normalize_decimal(df, column):
    """
    Normalise les séparateurs décimaux d'une colonne.

    Transforme les valeurs au format 'a,b' en 'a.b'.
    Les autres valeurs restent inchangées.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame contenant les données.
    column : str
        Nom de la colonne à normaliser.

    Returns
    -------
    None
        Modifie directement la colonne.

    Examples
    --------
    >>> normalize_decimal(df, "temperature")

    '12,5' -> '12.5'
    '20 mm' -> '20 mm'
    """
    mask = df[column].astype("string").str.fullmatch(
        r"-?\d+,\d+", na=False
    )

    df.loc[mask, column] = (
        df.loc[mask, column]
        .astype("string")
        .str.replace(",", ".", regex=False)
    )


def extract_units(df, column):
    """
    Extrait les unités associées aux valeurs numériques.

    Reconnaît les unités alphabétiques placées après
    un nombre entier ou décimal.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne contenant les valeurs avec unités.

    Returns
    -------
    pandas.Series
        Série contenant les unités extraites.
        Retourne None pour les valeurs sans unité reconnue.

    Examples
    --------
    >>> extract_units(df, "measurement")

    '20 mm'  -> 'mm'
    '12.5 C' -> 'C'
    '15'     -> None

    Notes
    -----
    Ne modifie pas le DataFrame.
    Ne reconnaît pas les unités avec caractères spéciaux,
    comme 'm²' ou 'kg/m3'.
    """
    def get_unit(value):
        if isinstance(value, str):
            match = re.fullmatch(
                r"-?\d+(?:[.,]\d+)?\s*([a-zA-Z]+)",
                value.strip()
            )
            if match:
                return match.group(1)
        return None

    return df[column].apply(get_unit)


def enleve_unit(df, column, unit):
    """
    Supprime uniquement l'unité spécifiée d'une colonne.

    Les observations portant une unité différente
    restent inchangées.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Nom de la colonne à traiter.
    unit : str
        Unité à supprimer, sans distinction de casse.

    Returns
    -------
    None
        Modifie directement la colonne.

    Examples
    --------
    >>> enleve_unit(df, "length", "mm")

    '20 mm' -> '20'
    '12mm'  -> '12'
    '15 kg' -> '15 kg'

    Notes
    -----
    Ne convertit pas les valeurs obtenues en type numérique.
    """
    pattern = rf"^\s*(-?\d+(?:[.,]\d+)?)\s*{re.escape(unit)}\s*$"

    mask = df[column].astype("string").str.fullmatch(
        pattern, case=False, na=False
    )

    df.loc[mask, column] = (
        df.loc[mask, column]
        .astype("string")
        .str.replace(pattern, r"\1", regex=True, flags=re.IGNORECASE)
    )


def detect_non_numeric(df, column):
    """
    Identifie les valeurs non numériques d'une colonne.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne à analyser.

    Returns
    -------
    pandas.Series
        Valeurs non convertibles en nombres.

    Examples
    --------
    >>> detect_non_numeric(df, "count")

    '12'    -> ignoré
    'abc'   -> détecté
    '15 kg' -> détecté

    Notes
    -----
    Ignore les valeurs manquantes.
    Ne modifie pas le DataFrame.
    """
    converted = pd.to_numeric(df[column], errors="coerce")

    mask = converted.isna() & df[column].notna()

    return df.loc[mask, column]


# ========================================================================
# Traitement des dates
# ========================================================================


def extract_datetime_format(df, column):
    """
    Identifie le format de date le plus fréquent dans une colonne.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne contenant les dates sous forme de chaînes.

    Returns
    -------
    str or None
        Format datetime dominant, ou None si aucun
        format connu n'est reconnu.

    Examples
    --------
    >>> extract_datetime_format(df, "survey_start")
    '%Y-%m-%dT%H:%M:%S'

    Notes
    -----
    Reconnaît la structure des dates sans valider
    leur existence dans le calendrier.

    Les formats DD/MM/YYYY et MM/DD/YYYY sont
    structurellement ambigus. La fonction actuelle
    privilégie DD/MM/YYYY.
    """
    formats = {
        "%Y-%m-%dT%H:%M:%S": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        "%Y-%m-%d %H:%M:%S": r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
        "%Y-%m-%d": r"\d{4}-\d{2}-\d{2}",
        "%d/%m/%Y": r"\d{2}/\d{2}/\d{4}",
        "%m/%d/%Y": r"\d{2}/\d{2}/\d{4}",
        "%Y/%m/%d": r"\d{4}/\d{2}/\d{2}",
        "%d-%m-%Y": r"\d{2}-\d{2}-\d{4}",
        "%Y-%m-%d %H:%M": r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}",
    }

    counts = {fmt: 0 for fmt in formats}

    for value in df[column].dropna().astype(str):
        value = value.strip()

        for fmt, pattern in formats.items():
            if re.fullmatch(pattern, value):
                counts[fmt] += 1
                break

    if max(counts.values()) == 0:
        return None

    return max(counts, key=counts.get)


def normalize_datetime(df, column, target_format):
    """
    Harmonise les dates d'une colonne.

    - Préserve les dates déjà au format ISO.
    - Convertit les autres formats reconnus.
    - Conserve les valeurs non convertibles.
    """

    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%b-%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y/%m/%d"
    ]

    def normalize_value(value):
        if pd.isna(value):
            return value

        from datetime import datetime

        value_str = str(value).strip()

        for fmt in formats:
            try:
                date = datetime.strptime(value_str, fmt)
                return date.strftime(target_format)
            except ValueError:
                continue

        return value

    df[column] = df[column].apply(normalize_value)


def detect_invalid_dates(df, column):
    """
    Détecte les valeurs ne pouvant pas être interprétées
    comme des dates valides.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne de dates à analyser.

    Returns
    -------
    pandas.Series
        Valeurs non convertibles en dates.

    Examples
    --------
    >>> detect_invalid_dates(df, "date")

    '2024-02-30' -> détecté
    'invalid'    -> détecté
    '2024-01-15' -> ignoré

    Notes
    -----
    Ignore les valeurs manquantes.
    Ne modifie pas le DataFrame.
    """
    dates = pd.to_datetime(
        df[column],
        format="mixed",
        errors="coerce",
        dayfirst=True
    )

    mask = dates.isna() & df[column].notna()

    return df.loc[mask, column]


def convert_datetime(df, column, date_format=None):
    """
    Convertit une colonne en type datetime pandas.

    Vérifie toutes les valeurs non manquantes avant
    d'effectuer la conversion.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne à convertir.
    date_format : str or None, optional
        Format d'entrée attendu.
        Si None, accepte des formats mélangés.

    Returns
    -------
    None
        Modifie directement la colonne.

    Raises
    ------
    ValueError
        Si une ou plusieurs valeurs ne peuvent pas
        être converties en dates valides.

    Examples
    --------
    >>> convert_datetime(df, "survey_start")
    >>> convert_datetime(df, "date", "%Y-%m-%d")

    Notes
    -----
    Les valeurs manquantes deviennent NaT.
    Aucune modification n'est effectuée si
    une date invalide est détectée.
    """
    dates = pd.to_datetime(
        df[column],
        format=date_format if date_format else "mixed",
        errors="coerce",
        dayfirst=True
    )

    mask_invalid = dates.isna() & df[column].notna()

    if mask_invalid.any():
        raise ValueError(
            f"Colonne '{column}' : {mask_invalid.sum()} dates invalides.\n"
            f"Valeurs : {df.loc[mask_invalid, column].unique().tolist()}"
        )

    df[column] = dates


def check_date_order(df, start_column, end_column):
    """
    Identifie les observations dont la date de début
    est postérieure à la date de fin.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    start_column : str
        Nom de la colonne de début.
    end_column : str
        Nom de la colonne de fin.

    Returns
    -------
    pandas.DataFrame
        Lignes pour lesquelles start_date > end_date.

    Examples
    --------
    >>> check_date_order(df, "survey_start", "survey_end")

    Notes
    -----
    Ne modifie pas le DataFrame.
    Les dates égales sont acceptées.
    Les comparaisons avec dates manquantes sont ignorées.
    Il est préférable de convertir les colonnes
    en datetime avant cette vérification.
    """
    start = pd.to_datetime(df[start_column], errors="raise")
    end = pd.to_datetime(df[end_column], errors="raise")

    mask = start.notna() & end.notna() & (start > end)

    return df.loc[mask]


# ========================================================================
# Exploration des données
# ========================================================================


def show_missing(df):
    """
    Résume les valeurs manquantes par colonne.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame à analyser.

    Returns
    -------
    pandas.DataFrame
        Tableau contenant :
        - missing_count : nombre de valeurs manquantes.
        - missing_percent : pourcentage de valeurs manquantes.

    Examples
    --------
    >>> show_missing(df)

    Notes
    -----
    Affiche uniquement les colonnes ayant des valeurs
    manquantes, triées par nombre décroissant.
    Ne modifie pas le DataFrame.
    """
    result = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_percent": df.isna().mean() * 100
    })

    result["missing_percent"] = result["missing_percent"].round(2)

    return result[result["missing_count"] > 0].sort_values(
        by="missing_count",
        ascending=False
    )


def show_unique_values(df, column):
    """
    Calcule la distribution des valeurs distinctes
    d'une colonne.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne à analyser.

    Returns
    -------
    pandas.DataFrame
        Tableau contenant :
        - count : fréquence absolue.
        - percent : fréquence relative en pourcentage.

    Examples
    --------
    >>> show_unique_values(df, "survey_method")

    Notes
    -----
    Inclut les valeurs manquantes.
    Trie les modalités par fréquence décroissante.
    Ne modifie pas le DataFrame.
    """
    counts = df[column].value_counts(dropna=False)

    result = pd.DataFrame({
        "count": counts,
        "percent": (counts / len(df) * 100).round(2)
    })

    return result


def complete_device_operations(df, source):
    """Complète les codes de panne et les prestataires manquants."""
    result = df.copy(deep=True)
    before = result.copy(deep=True)

    # Codes absents : aucune panne déclarée
    fault_mask = result["fault_code"].isna()

    assert result.loc[fault_mask, "maintenance_type"].eq(
        "routine inspection"
    ).all(), "Certains codes absents ne concernent pas une inspection de routine."

    result.loc[fault_mask, "fault_code"] = "NO_FAULT"

    # Repérer les opérations initialement sans prestataire
    missing_ids = source.loc[
        source["maintenance_provider"].isna(),
        "device_operation_id"
    ]

    provider_mask = result["device_operation_id"].isin(missing_ids)

    # Construire la correspondance à partir des valeurs non imputées
    providers_by_device = (
        result.loc[~provider_mask]
        .dropna(subset=["maintenance_provider"])
        .groupby("device_reference")
        .agg(
            nombre_prestataires=("maintenance_provider", "nunique"),
            prestataire_propose=("maintenance_provider", "first")
        )
    )

    mapping = providers_by_device.loc[
        providers_by_device["nombre_prestataires"].eq(1),
        "prestataire_propose"
    ]

    proposed = result.loc[
        provider_mask, "device_reference"
    ].map(mapping)

    assert proposed.notna().all(), (
        "Un prestataire unique ne peut pas être déterminé "
        "pour certains équipements."
    )

    result.loc[provider_mask, "maintenance_provider"] = proposed

    # Vérifier la structure et les valeurs conservées
    assert result.notna().all().all(), "Des valeurs manquantes subsistent."
    assert not result.duplicated().any()
    assert result["device_operation_id"].notna().all()
    assert result["device_operation_id"].is_unique
    assert len(result) == len(before)

    assert result["device_operation_id"].equals(
        before["device_operation_id"]
    )

    assert result.loc[~provider_mask, "maintenance_provider"].equals(
        before.loc[~provider_mask, "maintenance_provider"]
    )

    assert result.loc[~fault_mask, "fault_code"].equals(
        before.loc[~fault_mask, "fault_code"]
    )

    summary = {
        "Codes absents remplacés": int(fault_mask.sum()),
        "Prestataires initialement absents traités": int(provider_mask.sum()),
        "Valeurs manquantes restantes": int(result.isna().sum().sum()),
        "Observations conservées": len(result)
    }

    return result, summary

# ========================================================================
# Textes et catégories
# ========================================================================


def normalize_text(df, column):
    """
    Normalise les espaces dans une colonne textuelle.

    Supprime les espaces en début et fin de chaîne
    et remplace les séquences d'espaces par un seul.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne à normaliser.

    Returns
    -------
    None
        Modifie directement la colonne.

    Examples
    --------
    >>> normalize_text(df, "survey_method")

    '  Acoustic  ' -> 'Acoustic'
    'Visual   Survey' -> 'Visual Survey'

    Notes
    -----
    Ne modifie pas la casse des caractères.
    Ignore les valeurs qui ne sont pas des chaînes.
    """
    mask = df[column].map(lambda x: isinstance(x, str))

    df.loc[mask, column] = (
        df.loc[mask, column]
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )


def normalize_categories(df, column, mapping):
    """
    Harmonise les catégories d'une colonne à partir
    d'un dictionnaire de correspondance.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne catégorielle.
    mapping : dict
        Dictionnaire associant les anciennes valeurs
        aux nouvelles catégories.

    Returns
    -------
    None
        Modifie directement la colonne.

    Examples
    --------
    >>> mapping = {
    ...     "acoustic": "Acoustic",
    ...     "ACOUSTIC": "Acoustic"
    ... }
    >>> normalize_categories(df, "survey_method", mapping)

    Notes
    -----
    Les valeurs absentes du dictionnaire sont conservées.
    Les correspondances sont sensibles à la casse.
    """
    df[column] = df[column].replace(mapping)


def detect_rare_categories(df, column, threshold=0.05):
    """
    Détecte les catégories représentant une faible
    proportion des valeurs non manquantes.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne catégorielle.
    threshold : float, optional
        Seuil de fréquence relative.
        Valeur par défaut : 0.05 (5 %).

    Returns
    -------
    pandas.DataFrame
        Catégories rares avec :
        - count : effectif.
        - percent : pourcentage.

    Examples
    --------
    >>> detect_rare_categories(df, "survey_method", 0.05)

    Notes
    -----
    Exclut les valeurs manquantes du calcul.
    Ne supprime ni ne regroupe les catégories rares.
    """
    frequencies = df[column].value_counts(normalize=True, dropna=True)

    rare = frequencies[frequencies < threshold]

    return pd.DataFrame({
        "count": df[column].value_counts().reindex(rare.index),
        "percent": (rare * 100).round(2)
    })


# ========================================================================
# Détection des anomalies
# ========================================================================


def detect_outliers(df, column, factor=1.5):
    """
    Détecte les valeurs aberrantes selon la méthode IQR.

    Les bornes sont calculées comme suit :
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne numérique à analyser.
    factor : float, optional
        Multiplicateur de l'IQR.
        Valeur par défaut : 1.5.

    Returns
    -------
    pandas.DataFrame
        Observations situées hors des bornes IQR.

    Raises
    ------
    ValueError
        Si la colonne contient des valeurs non convertibles
        en nombres.

    Examples
    --------
    >>> detect_outliers(df, "observation_hours")
    >>> detect_outliers(df, "observation_hours", factor=3)

    Notes
    -----
    Les valeurs manquantes sont ignorées.
    Les outliers ne sont pas supprimés.
    """
    values = pd.to_numeric(df[column], errors="raise")

    Q1 = values.quantile(0.25)
    Q3 = values.quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR

    mask = (values < lower_bound) | (values > upper_bound)

    return df.loc[mask]


def check_numeric_range(df, column, min_value=None, max_value=None):
    """
    Détecte les valeurs situées hors d'un intervalle autorisé.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame source.
    column : str
        Colonne numérique à vérifier.
    min_value : int or float or None, optional
        Borne inférieure autorisée.
    max_value : int or float or None, optional
        Borne supérieure autorisée.

    Returns
    -------
    pandas.DataFrame
        Observations ne respectant pas les bornes.

    Examples
    --------
    >>> check_numeric_range(df, "count", min_value=0)
    >>> check_numeric_range(df, "temperature", -30, 60)

    Notes
    -----
    Les bornes sont inclusives.
    Les valeurs manquantes sont ignorées.
    Si les deux bornes sont None, retourne un DataFrame vide.
    Ne modifie pas les données.
    """
    values = pd.to_numeric(df[column], errors="raise")

    mask = pd.Series(False, index=df.index)

    if min_value is not None:
        mask |= values < min_value

    if max_value is not None:
        mask |= values > max_value

    return df.loc[mask]


def detect_category_variants(datasets, text_columns, exclude_columns):
    results = []

    for name, columns in text_columns.items():
        df = datasets[name]

        for col in columns:
            if col in exclude_columns:
                continue

            values = df[col].dropna().astype("string").unique()
            temp = pd.DataFrame({"original": values})

            temp["normalized"] = (
                temp["original"]
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
                .str.lower()
            )

            groups = temp.groupby("normalized")["original"].agg(list)

            for normalized, variants in groups.items():
                if len(variants) > 1:
                    results.append({
                        "dataset": name,
                        "column": col,
                        "normalized": normalized,
                        "variants": variants
                    })

    return pd.DataFrame(
        results,
        columns=["dataset", "column", "normalized", "variants"]
    )


def summarize_outliers(df, columns, factor=1.5):
    """Résume les valeurs atypiques IQR sans modifier les données."""
    results = []

    for col in columns:
        values = pd.to_numeric(df[col], errors="raise").dropna()

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1

        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        count = int((values.lt(lower) | values.gt(upper)).sum())

        results.append({
            "variable": col,
            "nombre_renseigne": len(values),
            "Q1": q1,
            "Q3": q3,
            "borne_inferieure": lower,
            "borne_superieure": upper,
            "nombre_atypiques": count,
            "pourcentage_atypiques": (
                100 * count / len(values) if len(values) else float("nan")
            )
        })

    return pd.DataFrame(results)


def summarize_categories(df, column):
    """Compte les observations et leur proportion par catégorie."""
    counts = df[column].value_counts(dropna=False)

    return pd.DataFrame({
        "effectif": counts,
        "pourcentage": (counts / len(df) * 100).round(2)
    }).rename_axis(column)


def plot_site_distributions(sites):
    """Présente les habitats et les types de suivi par région."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Répartition des habitats
    habitats = sites["habitat_category"].value_counts().sort_values()

    habitats.plot.barh(ax=axes[0], color="steelblue")

    axes[0].set_title("Répartition des sites par habitat")
    axes[0].set_xlabel("Nombre de sites")
    axes[0].set_ylabel("")
    axes[0].bar_label(axes[0].containers[0], padding=3)
    axes[0].set_xlim(0, habitats.max() * 1.2)

    # Types de suivi dans chaque région
    regions = {
        "Eastern Avelora Agricultural Cluster": "Est d’Avelora",
        "Kintara Karst Cluster": "Kintara",
        "Tembara Coastal Cluster": "Tembara"
    }

    categories = {
        "cave monitoring": "Grottes",
        "habitat monitoring": "Habitats",
        "orchard monitoring": "Vergers"
    }

    counts = pd.crosstab(
        sites["region"],
        sites["site_category"]
    ).rename(index=regions, columns=categories)

    counts.plot.bar(
        ax=axes[1],
        stacked=True,
        color=["#8064A2", "#4C956C", "#E5AE38"]
    )

    axes[1].set_title("Types de suivi par région")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Nombre de sites")
    axes[1].tick_params(axis="x", labelrotation=0)
    axes[1].legend(title="Type de suivi")

    fig.tight_layout()
    plt.show()


def summarize_survey_coverage(surveys):
    """Résume la période et le nombre de mois suivis par site."""
    data = surveys.copy()
    data["month"] = data["survey_start"].dt.to_period("M")

    return (
        data.groupby("site_code")
        .agg(
            nombre_releves=("survey_id", "size"),
            nombre_mois=("month", "nunique"),
            premier_releve=("survey_start", "min"),
            dernier_releve=("survey_start", "max")
        )
    )


def add_bat_observation_rate(surveys):
    """Ajoute le nombre de chauves-souris observées par heure."""
    data = surveys.copy()

    hours = data["observation_hours"]

    if hours.isna().any() or hours.le(0).any():
        raise ValueError(
            "Les heures d’observation doivent être renseignées "
            "et strictement positives."
        )

    data["bats_per_hour"] = data["observed_bat_count"] / hours

    return data


def plot_monthly_bat_activity(surveys):
    """Trace la médiane mensuelle et les quartiles entre sites."""
    import matplotlib.pyplot as plt

    data = surveys.copy()
    data["month"] = (
        data["survey_start"].dt.to_period("M").dt.to_timestamp()
    )

    monthly = (
        data.groupby("month")["bats_per_hour"]
        .agg(
            mediane="median",
            q1=lambda values: values.quantile(0.25),
            q3=lambda values: values.quantile(0.75)
        )
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        monthly.index,
        monthly["mediane"],
        color="steelblue",
        label="Médiane des sites"
    )

    ax.fill_between(
        monthly.index,
        monthly["q1"].to_numpy(),
        monthly["q3"].to_numpy(),
        color="steelblue",
        alpha=0.2,
        label="Premier au troisième quartile"
    )

    ax.set_title("Évolution mensuelle de l’activité observée")
    ax.set_xlabel("Date")
    ax.set_ylabel("Chauves-souris observées par heure")
    ax.set_ylim(bottom=0)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()

    return monthly


def plot_bat_seasonality(monthly_activity):
    """Compare les médianes mensuelles selon le mois de l’année."""
    import matplotlib.pyplot as plt

    data = monthly_activity.copy()
    data["mois"] = data.index.month

    values = [
        data.loc[data["mois"].eq(month), "mediane"].to_numpy()
        for month in range(1, 13)
    ]

    labels = [
        "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
        "Juil", "Août", "Sep", "Oct", "Nov", "Déc"
    ]

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.boxplot(values, tick_labels=labels)

    ax.set_title("Activité observée selon le mois de l’année")
    ax.set_xlabel("Mois")
    ax.set_ylabel("Médiane des sites — observations par heure")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()


def plot_bat_activity_by_region(surveys, sites):
    """Compare les médianes mensuelles des trois régions."""
    import matplotlib.pyplot as plt

    data = surveys.merge(
        sites[["site_code", "region"]],
        on="site_code",
        how="left",
        validate="many_to_one"
    )

    if data["region"].isna().any():
        raise ValueError("Certains sites n’ont pas de région associée.")

    data["month"] = (
        data["survey_start"].dt.to_period("M").dt.to_timestamp()
    )

    monthly = (
        data.groupby(["month", "region"])["bats_per_hour"]
        .median()
        .unstack("region")
        .rename(columns={
            "Eastern Avelora Agricultural Cluster": "Est d’Avelora",
            "Kintara Karst Cluster": "Kintara",
            "Tembara Coastal Cluster": "Tembara"
        })
    )

    ax = monthly.plot(figsize=(12, 5))

    ax.set_title("Évolution de l’activité observée par région")
    ax.set_xlabel("Date")
    ax.set_ylabel("Médiane des observations par heure")
    ax.set_ylim(bottom=0)
    ax.legend(title="Région")
    ax.grid(axis="y", alpha=0.3)

    ax.figure.tight_layout()
    plt.show()

    return monthly


def summarize_bat_activity_by_site(surveys, sites):
    """Résume le niveau et la variation de l’activité par site."""
    summary = (
        surveys.groupby("site_code")["bats_per_hour"]
        .agg(
            mediane="median",
            q10=lambda values: values.quantile(0.10),
            q90=lambda values: values.quantile(0.90)
        )
        .reset_index()
    )

    summary["amplitude_centrale"] = summary["q90"] - summary["q10"]

    return (
        summary.merge(
            sites[["site_code", "region", "site_category"]],
            on="site_code",
            how="left",
            validate="one_to_one"
        )
        .sort_values("amplitude_centrale", ascending=False)
        .reset_index(drop=True)
    )


def plot_selected_site_activity(surveys, site_codes):
    """Trace séparément l’activité des sites sélectionnés."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(
        len(site_codes),
        1,
        figsize=(12, 3 * len(site_codes)),
        sharex=True,
        sharey=True,
        squeeze=False
    )

    for ax, site_code in zip(axes[:, 0], site_codes):
        data = (
            surveys.loc[surveys["site_code"].eq(site_code)]
            .sort_values("survey_start")
        )

        ax.plot(
            data["survey_start"],
            data["bats_per_hour"],
            color="steelblue"
        )

        ax.set_title(site_code)
        ax.set_ylabel("Observations / heure")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.3)

    axes[-1, 0].set_xlabel("Date")

    fig.tight_layout()
    plt.show()


def link_surveys_to_devices(surveys, operations):
    """Relie les relevés aux appareils par site et mois."""
    surveys = surveys.copy()
    operations = operations.copy()

    surveys["month"] = (
        surveys["survey_start"].dt.to_period("M")
    )

    operations["month"] = (
        operations["operation_start"].dt.to_period("M")
    )

    columns = [
        "site_code",
        "month",
        "uptime_pct",
        "acoustic_quality",
        "fault_code",
        "maintenance_type"
    ]

    return surveys.merge(
        operations[columns],
        on=["site_code", "month"],
        how="left",
        validate="one_to_one",
        indicator="device_match"
    )


def plot_activity_and_device_quality(data, site_codes):
    """Compare l’activité et le fonctionnement des appareils."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(
        len(site_codes),
        2,
        figsize=(14, 3 * len(site_codes)),
        sharex=True,
        squeeze=False
    )

    for row, site_code in enumerate(site_codes):
        site = (
            data.loc[data["site_code"].eq(site_code)]
            .sort_values("survey_start")
        )

        activity_ax = axes[row, 0]
        quality_ax = axes[row, 1]

        activity_ax.plot(
            site["survey_start"],
            site["bats_per_hour"],
            color="steelblue"
        )
        activity_ax.set_title(f"{site_code} — activité")
        activity_ax.set_ylabel("Observations / heure")
        activity_ax.set_ylim(bottom=0)

        quality_ax.plot(
            site["survey_start"],
            site["uptime_pct"],
            label="Disponibilité (%)",
            color="darkorange"
        )
        quality_ax.plot(
            site["survey_start"],
            site["acoustic_quality"],
            label="Qualité acoustique (score)",
            color="seagreen"
        )
        quality_ax.set_title(f"{site_code} — appareil")
        quality_ax.set_ylabel("Valeur")
        quality_ax.legend(fontsize=8)

        for ax in axes[row]:
            ax.grid(alpha=0.3)

    for ax in axes[-1]:
        ax.set_xlabel("Date")

    fig.tight_layout()
    plt.show()


def summarize_device_correlations(data, site_codes):
    """Calcule les corrélations de Spearman pour chaque site."""
    results = []

    for site_code in site_codes:
        site = data.loc[data["site_code"].eq(site_code)]

        for variable in ["uptime_pct", "acoustic_quality"]:
            pairs = site[
                ["bats_per_hour", variable]
            ].dropna()

            results.append({
                "site_code": site_code,
                "indicateur": variable,
                "nombre_paires": len(pairs),
                "spearman": pairs["bats_per_hour"].corr(
                    pairs[variable],
                    method="spearman"
                )
            })

    return pd.DataFrame(results)


def link_surveys_to_environment(surveys, environment):
    """Associe les conditions environnementales sans perdre de relevés."""
    surveys = surveys.copy()
    environment = environment.copy()

    surveys["month"] = (
        surveys["survey_start"].dt.to_period("M")
    )

    environment["month"] = (
        environment["reporting_month"].dt.to_period("M")
    )

    return surveys.merge(
        environment.drop(columns=["reporting_month"]),
        on=["site_code", "month"],
        how="left",
        validate="one_to_one",
        indicator="environment_match"
    )


def correlations_by_site(data, site_codes, variables,
                         target="bats_per_hour"):
    """Calcule les corrélations de Spearman par site."""
    results = []

    for site_code in site_codes:
        site = data.loc[data["site_code"].eq(site_code)]

        for variable in variables:
            pairs = site[[target, variable]].dropna()

            results.append({
                "site_code": site_code,
                "variable": variable,
                "nombre_paires": len(pairs),
                "spearman": pairs[target].corr(
                    pairs[variable],
                    method="spearman"
                )
            })

    return pd.DataFrame(results)


def plot_environment_correlations(
        correlations,
        title="Activité et environnement — corrélations de Spearman"):
    """Affiche les corrélations par variable et par site."""
    import matplotlib.pyplot as plt

    labels = {
        "mean_temperature_c": "Température",
        "rainfall_mm": "Pluie",
        "mean_humidity_pct": "Humidité",
        "vegetation_cover_pct": "Couverture végétale",
        "habitat_disturbance_index": "Perturbation de l’habitat",
        "pesticide_index": "Pesticides"
    }

    matrix = (
        correlations.pivot(
            index="variable",
            columns="site_code",
            values="spearman"
        )
        .reindex(list(labels))
        .rename(index=labels)
    )

    fig, ax = plt.subplots(figsize=(8, 5))

    heatmap = ax.imshow(
        matrix.to_numpy(),
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        aspect="auto"
    )

    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns)

    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)

    for row in range(len(matrix.index)):
        for col in range(len(matrix.columns)):
            value = matrix.iloc[row, col]

            ax.text(
                col, row,
                f"{value:.2f}" if pd.notna(value) else "n.d.",
                ha="center",
                va="center",
                color="white" if abs(value) >= 0.6 else "black"
            )

    ax.set_title(title)
    fig.colorbar(heatmap, ax=ax, label="Corrélation de Spearman")
    fig.tight_layout()
    plt.show()


def plot_selected_environment_relationships(data):
    """Trace quatre relations repérées dans les corrélations."""
    import matplotlib.pyplot as plt

    comparisons = [
        ("KNT-VLB", "mean_temperature_c", "Température moyenne (°C)"),
        ("KNT-KES", "mean_temperature_c", "Température moyenne (°C)"),
        ("TMB-BRC", "pesticide_index", "Indice de pesticides"),
        ("KNT-KES", "pesticide_index", "Indice de pesticides")
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    for ax, (site_code, variable, label) in zip(
        axes.flat, comparisons
    ):
        site = data.loc[data["site_code"].eq(site_code)]

        ax.scatter(
            site[variable],
            site["bats_per_hour"],
            color="steelblue",
            alpha=0.65
        )

        ax.set_title(site_code)
        ax.set_xlabel(label)
        ax.set_ylabel("Observations / heure")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.3)

    fig.tight_layout()
    plt.show()


def remove_average_seasonality(data, variables):
    """Calcule les écarts au profil mensuel moyen de chaque site."""
    result = data.copy()
    result["calendar_month"] = result["survey_start"].dt.month

    for variable in variables:
        seasonal_mean = (
            result.groupby(["site_code", "calendar_month"])[variable]
            .transform("mean")
        )

        result[f"{variable}_deviation"] = (
            result[variable] - seasonal_mean
        )

    return result


def plot_correlation_distributions(raw, adjusted):
    """Compare les corrélations brutes et désaisonnalisées par site."""
    import matplotlib.pyplot as plt

    labels = {
        "mean_temperature_c": "Température",
        "rainfall_mm": "Pluie",
        "mean_humidity_pct": "Humidité",
        "vegetation_cover_pct": "Couverture végétale",
        "habitat_disturbance_index": "Perturbation de l’habitat",
        "pesticide_index": "Pesticides"
    }

    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharey=True)

    for ax, (variable, label) in zip(axes.flat, labels.items()):
        before = raw.loc[
            raw["variable"].eq(variable), "spearman"
        ].dropna()

        after = adjusted.loc[
            adjusted["variable"].eq(variable), "spearman"
        ].dropna()

        ax.boxplot(
            [before, after],
            tick_labels=["Brutes", "Écarts saisonniers"]
        )

        ax.axhline(0, color="grey", linestyle="--", linewidth=1)
        ax.set_title(label)
        ax.set_ylim(-1, 1)
        ax.grid(axis="y", alpha=0.3)

    for ax in axes[:, 0]:
        ax.set_ylabel("Corrélation de Spearman")

    fig.tight_layout()
    plt.show()


def prepare_orchard_analysis(orchards, bat_environment):
    """Associe les vergers au suivi et calcule le rendement par hectare."""
    orchards = orchards.copy()

    orchards["month"] = (
        orchards["survey_period"].dt.to_period("M")
    )

    columns = [
        "site_code",
        "month",
        "bats_per_hour",
        "mean_temperature_c",
        "rainfall_mm",
        "pesticide_index"
    ]

    data = orchards.merge(
        bat_environment[columns],
        on=["site_code", "month"],
        how="left",
        validate="one_to_one"
    )

    area = data["orchard_area_ha"].where(
        data["orchard_area_ha"].gt(0)
    )

    data["yield_kg_per_ha"] = data["durian_yield_kg"] / area

    return data


def plot_orchard_relationships(data):
    """Compare l’activité à la fructification et au rendement."""
    import matplotlib.pyplot as plt

    variables = {
        "fruit_set_rate_pct": "Taux de fructification (%)",
        "yield_kg_per_ha": "Rendement (kg/ha)"
    }

    site_codes = sorted(data["site_code"].unique())
    colors = plt.get_cmap("tab20")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for index, site_code in enumerate(site_codes):
        site = data.loc[data["site_code"].eq(site_code)]

        for ax, (variable, label) in zip(axes, variables.items()):
            ax.scatter(
                site["bats_per_hour"],
                site[variable],
                color=colors(index % 20),
                alpha=0.5,
                s=18,
                label=site_code
            )

            ax.set_xlabel("Chauves-souris observées par heure")
            ax.set_ylabel(label)
            ax.set_ylim(bottom=0)
            ax.grid(alpha=0.3)

    axes[0].set_title("Activité et fructification")
    axes[1].set_title("Activité et rendement")

    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        title="Site",
        loc="center left",
        bbox_to_anchor=(0.86, 0.5),
        fontsize=8
    )

    fig.tight_layout(rect=[0, 0, 0.86, 1])
    plt.show()


def plot_orchard_correlations(data):
    """Compare les corrélations par verger et leur sensibilité."""
    import matplotlib.pyplot as plt

    results = []

    for site_code, site in data.groupby("site_code"):
        fruit = site[
            ["bats_per_hour", "fruit_set_rate_pct"]
        ].dropna()

        suspect = fruit["fruit_set_rate_pct"].between(
            0, 1, inclusive="neither"
        )
        fruit_without_suspects = fruit.loc[~suspect]

        yield_data = site[
            ["bats_per_hour", "yield_kg_per_ha"]
        ].dropna()

        results.append({
            "site_code": site_code,
            "fructification": fruit["bats_per_hour"].corr(
                fruit["fruit_set_rate_pct"], method="spearman"
            ),
            "fructification_sans_taux_suspects":
                fruit_without_suspects["bats_per_hour"].corr(
                    fruit_without_suspects["fruit_set_rate_pct"],
                    method="spearman"
            ),
            "rendement": yield_data["bats_per_hour"].corr(
                yield_data["yield_kg_per_ha"], method="spearman"
            )
        })

    summary = pd.DataFrame(results).set_index("site_code")

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.boxplot(
        [summary[col].dropna() for col in summary.columns],
        tick_labels=[
            "Fructification\nToutes les valeurs",
            "Fructification\nSans taux suspects",
            "Rendement\nToutes les valeurs"
        ]
    )

    ax.axhline(0, color="grey", linestyle="--")
    ax.set_ylim(-1, 1)
    ax.set_ylabel("Corrélation de Spearman")
    ax.set_title("Associations avec l’activité — comparaison entre vergers")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()

    return summary


def plot_orchard_seasonal_comparison(data):
    """Compare les associations par verger avant et après saisonnalité."""
    import matplotlib.pyplot as plt

    data = data.copy()
    data["calendar_month"] = data["survey_period"].dt.month

    # Écarter les taux incertains pour cette comparaison uniquement
    suspect = data["fruit_set_rate_pct"].between(
        0, 1, inclusive="neither"
    )
    data["fruit_set_rate_pct"] = (
        data["fruit_set_rate_pct"].mask(suspect)
    )

    targets = {
        "fruit_set_rate_pct": "Fructification",
        "yield_kg_per_ha": "Rendement par hectare"
    }

    results = []

    for site_code, site in data.groupby("site_code"):
        for variable, label in targets.items():
            pairs = site[
                ["calendar_month", "bats_per_hour", variable]
            ].dropna()

            values = pairs[["bats_per_hour", variable]]

            deviations = values - (
                pairs.groupby("calendar_month")[
                    ["bats_per_hour", variable]
                ].transform("mean")
            )

            results.append({
                "site_code": site_code,
                "indicateur": label,
                "brute": values["bats_per_hour"].corr(
                    values[variable], method="spearman"
                ),
                "apres_saisonnalite": deviations["bats_per_hour"].corr(
                    deviations[variable], method="spearman"
                )
            })

    summary = pd.DataFrame(results)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

    for ax, label in zip(axes, targets.values()):
        subset = summary.loc[summary["indicateur"].eq(label)]

        ax.boxplot(
            [
                subset["brute"].dropna(),
                subset["apres_saisonnalite"].dropna()
            ],
            tick_labels=["Brutes", "Écarts saisonniers"]
        )

        ax.set_title(label)
        ax.axhline(0, color="grey", linestyle="--")
        ax.set_ylim(-1, 1)
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_ylabel("Corrélation de Spearman")

    fig.tight_layout()
    plt.show()

    return summary


def summarize_comparable_site_groups(sites):
    """Regroupe les sites par région, type de suivi et habitat."""
    criteria = [
        "region",
        "site_category",
        "habitat_category"
    ]

    return (
        sites.groupby(criteria, dropna=False)
        .agg(
            nombre_sites=("site_code", "nunique"),
            sites=(
                "site_code",
                lambda codes: ", ".join(sorted(codes.unique()))
            )
        )
        .reset_index()
        .sort_values("nombre_sites", ascending=False)
        .reset_index(drop=True)
    )


def plot_device_correlation_distributions(correlations):
    """Présente les corrélations techniques calculées par site."""
    import matplotlib.pyplot as plt

    variables = {
        "uptime_pct": "Disponibilité",
        "acoustic_quality": "Qualité acoustique"
    }

    values = [
        correlations.loc[
            correlations["variable"].eq(variable), "spearman"
        ].dropna()
        for variable in variables
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.boxplot(values, tick_labels=list(variables.values()))
    ax.axhline(0, color="grey", linestyle="--")
    ax.set_ylim(-1, 1)
    ax.set_ylabel("Corrélation de Spearman")
    ax.set_title("Activité et fonctionnement des appareils — 64 sites")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()


def compare_declared_faults(data):
    """Compare les relevés avec panne à une référence site-saison."""
    import matplotlib.pyplot as plt

    data = data.copy()
    data["calendar_month"] = data["survey_start"].dt.month

    variables = {
        "bats_per_hour": "Activité\n(observations / heure)",
        "uptime_pct": "Disponibilité\n(points de pourcentage)",
        "acoustic_quality": "Qualité acoustique\n(points de score)"
    }

    faults = {
        "MICROPHONE_DRIFT": "Microphone",
        "STORAGE_LIMIT": "Stockage",
        "POWER_INTERRUPTION": "Alimentation"
    }

    reference = (
        data.loc[data["fault_code"].eq("NO_FAULT")]
        .groupby(["site_code", "calendar_month"])[list(variables)]
        .median()
        .add_suffix("_reference")
        .reset_index()
    )

    comparison = (
        data.loc[data["fault_code"].isin(faults)]
        .merge(
            reference,
            on=["site_code", "calendar_month"],
            how="left",
            validate="many_to_one"
        )
    )

    for variable in variables:
        comparison[f"{variable}_difference"] = (
            comparison[variable]
            - comparison[f"{variable}_reference"]
        )

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    for ax, (variable, label) in zip(axes, variables.items()):
        values = [
            comparison.loc[
                comparison["fault_code"].eq(code),
                f"{variable}_difference"
            ].dropna()
            for code in faults
        ]

        ax.boxplot(values, tick_labels=list(faults.values()))
        ax.axhline(0, color="grey", linestyle="--")
        ax.set_ylabel(f"Écart à la référence — {label}")
        ax.tick_params(axis="x", labelrotation=20)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(
        "Pannes déclarées : comparaison au même site et à la même saison")
    fig.tight_layout()
    plt.show()

    return comparison


def summarize_maintenance_providers(operations):
    """Décrit les prestataires et leurs affectations aux sites."""
    summary = (
        operations.groupby("maintenance_provider")
        .agg(
            nombre_operations=("device_operation_id", "size"),
            nombre_sites=("site_code", "nunique"),
            nombre_appareils=("device_reference", "nunique")
        )
        .sort_values("nombre_sites", ascending=False)
    )

    providers_per_site = (
        operations.groupby("site_code")["maintenance_provider"]
        .nunique()
        .rename("nombre_prestataires")
    )

    return summary, providers_per_site


def plot_maintenance_provider_comparison(data, operations):
    """Compare les indicateurs techniques par site et prestataire."""
    import matplotlib.pyplot as plt

    assignments = operations[
        ["site_code", "maintenance_provider"]
    ].drop_duplicates()

    linked = data.merge(
        assignments,
        on="site_code",
        how="left",
        validate="many_to_one"
    )

    linked["declared_fault"] = linked["fault_code"].isin([
        "MICROPHONE_DRIFT",
        "STORAGE_LIMIT",
        "POWER_INTERRUPTION"
    ])

    summary = (
        linked.groupby(["maintenance_provider", "site_code"])
        .agg(
            disponibilite_mediane=("uptime_pct", "median"),
            qualite_mediane=("acoustic_quality", "median"),
            pannes_pct=("declared_fault", lambda values: 100 * values.mean())
        )
        .reset_index()
    )

    indicators = {
        "disponibilite_mediane": "Disponibilité médiane (%)",
        "qualite_mediane": "Qualité acoustique médiane (score)",
        "pannes_pct": "Relevés avec panne déclarée (%)"
    }

    providers = sorted(summary["maintenance_provider"].unique())

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    for ax, (variable, label) in zip(axes, indicators.items()):
        values = [
            summary.loc[
                summary["maintenance_provider"].eq(provider),
                variable
            ].dropna()
            for provider in providers
        ]

        ax.boxplot(
            values,
            tick_labels=[
                provider.replace("ECO-SERVICE-", "Service ")
                for provider in providers
            ]
        )

        ax.set_title(label)
        ax.tick_params(axis="x", labelrotation=25)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(
        "Indicateurs techniques par prestataire — une valeur par site")
    fig.tight_layout()
    plt.show()

    return summary


def plot_orchard_factor_correlations(data):
    """Compare les associations agricoles après retrait de la saisonnalité."""
    import matplotlib.pyplot as plt

    data = data.copy()
    data["calendar_month"] = data["survey_period"].dt.month

    suspect = data["fruit_set_rate_pct"].between(
        0, 1, inclusive="neither"
    )
    data["fruit_set_rate_pct"] = (
        data["fruit_set_rate_pct"].mask(suspect)
    )

    factors = {
        "pesticide_index": "Pesticides",
        "fertilizer_use_index": "Fertilisation",
        "irrigation_level": "Irrigation",
        "durian_flower_density": "Densité florale",
        "other_pollinator_activity": "Autres pollinisateurs"
    }

    targets = {
        "fruit_set_rate_pct": "Fructification",
        "yield_kg_per_ha": "Rendement par hectare"
    }

    results = []

    for site_code, site in data.groupby("site_code"):
        for target in targets:
            for factor in factors:
                pairs = site[
                    ["calendar_month", target, factor]
                ].dropna()

                deviations = pairs[[target, factor]] - (
                    pairs.groupby("calendar_month")[
                        [target, factor]
                    ].transform("mean")
                )

                results.append({
                    "site_code": site_code,
                    "indicateur": target,
                    "facteur": factor,
                    "spearman": deviations[target].corr(
                        deviations[factor],
                        method="spearman"
                    )
                })

    summary = pd.DataFrame(results)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True)

    for ax, (target, title) in zip(axes, targets.items()):
        values = [
            summary.loc[
                summary["indicateur"].eq(target)
                & summary["facteur"].eq(factor),
                "spearman"
            ].dropna()
            for factor in factors
        ]

        ax.boxplot(values, tick_labels=list(factors.values()))
        ax.axhline(0, color="grey", linestyle="--")
        ax.set_title(title)
        ax.set_ylim(-1, 1)
        ax.tick_params(axis="x", labelrotation=35)
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_ylabel("Corrélation de Spearman")
    fig.suptitle("Facteurs agricoles — écarts au profil saisonnier moyen")
    fig.tight_layout()
    plt.show()

    return summary


def build_access_windows(accesses, surveys):
    """Retrouve les trois mois avant et après chaque accès."""
    observations = surveys[
        ["site_code", "survey_start", "bats_per_hour"]
    ].copy()

    observations["month"] = (
        observations["survey_start"].dt.to_period("M")
    )

    windows = []
    summaries = []

    for event in accesses.itertuples(index=False):
        access_month = event.event_time.to_period("M")
        offsets = [-3, -2, -1, 1, 2, 3]

        window = pd.DataFrame({
            "relative_month": offsets,
            "month": [access_month + offset for offset in offsets]
        })

        window["site_code"] = event.site_code

        window = window.merge(
            observations.drop(columns="survey_start"),
            on=["site_code", "month"],
            how="left",
            validate="one_to_one"
        )

        window["access_case_number"] = event.access_case_number
        windows.append(window)

        before = window.loc[
            window["relative_month"].lt(0), "bats_per_hour"
        ]
        after = window.loc[
            window["relative_month"].gt(0), "bats_per_hour"
        ]

        summaries.append({
            "access_case_number": event.access_case_number,
            "site_code": event.site_code,
            "access_date": event.event_time,
            "organization": event.requesting_organization_name,
            "mois_avant": before.count(),
            "mois_apres": after.count(),
            "fenetre_complete": (
                before.count() == 3 and after.count() == 3
            )
        })

    return pd.concat(windows, ignore_index=True), pd.DataFrame(summaries)


def plot_access_before_after(windows, eligible):
    """Compare les médianes d’activité avant et après chaque accès."""
    import matplotlib.pyplot as plt

    data = windows.loc[
        windows["access_case_number"].isin(
            eligible["access_case_number"]
        )
    ].copy()

    data["period"] = data["relative_month"].map(
        lambda month: "avant" if month < 0 else "apres"
    )

    activity = (
        data.groupby(["access_case_number", "period"])["bats_per_hour"]
        .median()
        .unstack("period")
        .reset_index()
    )

    comparison = eligible.merge(
        activity,
        on="access_case_number",
        validate="one_to_one"
    )

    comparison["difference"] = (
        comparison["apres"] - comparison["avant"]
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    limit = comparison[["avant", "apres"]].max().max() * 1.05

    axes[0].scatter(
        comparison["avant"],
        comparison["apres"],
        color="steelblue",
        alpha=0.7
    )
    axes[0].plot([0, limit], [0, limit], "--", color="grey")
    axes[0].set_xlim(0, limit)
    axes[0].set_ylim(0, limit)
    axes[0].set_aspect("equal", adjustable="box")
    axes[0].set_xlabel("Avant — observations / heure")
    axes[0].set_ylabel("Après — observations / heure")
    axes[0].set_title("Activité médiane par accès")

    axes[1].hist(
        comparison["difference"],
        bins=12,
        color="steelblue",
        edgecolor="white"
    )
    axes[1].axvline(0, color="grey", linestyle="--")
    axes[1].set_xlabel("Différence après − avant (observations / heure)")
    axes[1].set_ylabel("Nombre d’accès")
    axes[1].set_title("Distribution des variations")

    fig.tight_layout()
    plt.show()

    return comparison


def compare_access_seasonality(windows, eligible, surveys, raw_comparison):
    """Compare les variations brutes aux variations corrigées de saison."""
    import matplotlib.pyplot as plt

    surveys = surveys.copy()
    surveys["month"] = surveys["survey_start"].dt.to_period("M")

    results = []

    for event in eligible.itertuples(index=False):
        access_month = event.access_date.to_period("M")

        site = surveys.loc[
            surveys["site_code"].eq(event.site_code)
        ]

        excluded_months = [
            access_month + offset for offset in range(-3, 4)
        ]

        reference_data = site.loc[
            ~site["month"].isin(excluded_months)
        ]

        reference = reference_data.groupby(
            reference_data["month"].dt.month
        )["bats_per_hour"].median()

        window = windows.loc[
            windows["access_case_number"].eq(event.access_case_number)
        ].copy()

        window["reference"] = window["month"].dt.month.map(reference)
        window["deviation"] = (
            window["bats_per_hour"] - window["reference"]
        )

        before = window.loc[
            window["relative_month"].lt(0), "deviation"
        ].median()

        after = window.loc[
            window["relative_month"].gt(0), "deviation"
        ].median()

        results.append({
            "access_case_number": event.access_case_number,
            "difference_saisonniere": after - before
        })

    comparison = raw_comparison.merge(
        pd.DataFrame(results),
        on="access_case_number",
        validate="one_to_one"
    )

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.boxplot(
        [
            comparison["difference"].dropna(),
            comparison["difference_saisonniere"].dropna()
        ],
        tick_labels=["Variation brute", "Écarts saisonniers"]
    )

    ax.axhline(0, color="grey", linestyle="--")
    ax.set_ylabel("Différence après − avant (observations / heure)")
    ax.set_title("Variations autour des accès")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()

    return comparison


def find_access_comparison_sites(eligible, sites, all_accesses):
    """Recherche des sites comparables sans accès proche enregistré."""
    criteria = ["region", "site_category", "habitat_category"]

    descriptions = sites.set_index("site_code")
    accesses = all_accesses.copy()
    accesses["access_month"] = (
        accesses["event_time"].dt.to_period("M")
    )

    results = []

    for event in eligible.itertuples(index=False):
        access_month = event.access_date.to_period("M")
        description = descriptions.loc[event.site_code]

        similar = sites.loc[
            sites[criteria].eq(description[criteria]).all(axis=1)
            & sites["site_code"].ne(event.site_code),
            "site_code"
        ]

        nearby_accesses = accesses.loc[
            accesses["access_month"].between(
                access_month - 3,
                access_month + 3
            ),
            "site_code"
        ]

        comparison_sites = similar.loc[
            ~similar.isin(nearby_accesses)
        ].tolist()

        results.append({
            "access_case_number": event.access_case_number,
            "site_code": event.site_code,
            "organization": event.organization,
            "nombre_comparateurs": len(comparison_sites),
            "sites_comparateurs": comparison_sites
        })

    return pd.DataFrame(results)


def seasonal_site_window_change(surveys, site_code, access_date):
    """Calcule la variation saisonnière autour d’une date sur un site."""
    site = surveys.loc[
        surveys["site_code"].eq(site_code)
    ].copy()

    site["month"] = site["survey_start"].dt.to_period("M")
    access_month = access_date.to_period("M")

    offsets = [-3, -2, -1, 1, 2, 3]
    months = [access_month + offset for offset in offsets]

    reference_data = site.loc[
        ~site["month"].isin([
            access_month + offset for offset in range(-3, 4)
        ])
    ]

    reference = reference_data.groupby(
        reference_data["month"].dt.month
    )["bats_per_hour"].median()

    observed = site.set_index("month")["bats_per_hour"].reindex(months)

    expected = pd.Series(
        [reference.get(month.month, float("nan")) for month in months],
        index=months
    )

    deviations = observed - expected

    if deviations.isna().any():
        return float("nan")

    return deviations.iloc[3:].median() - deviations.iloc[:3].median()


def compare_access_peer_variations(comparison, comparators, surveys):
    """Compare chaque accès à la variation médiane de ses comparateurs."""
    data = comparison.merge(
        comparators[["access_case_number", "sites_comparateurs"]],
        on="access_case_number",
        validate="one_to_one"
    )

    results = []

    for event in data.itertuples(index=False):
        peer_changes = pd.Series([
            seasonal_site_window_change(
                surveys, site_code, event.access_date
            )
            for site_code in event.sites_comparateurs
        ], dtype=float).dropna()

        peer_median = peer_changes.median()

        results.append({
            "access_case_number": event.access_case_number,
            "comparateurs_utilises": len(peer_changes),
            "variation_comparateurs": peer_median,
            "difference_relative": (
                event.difference_saisonniere - peer_median
            )
        })

    return comparison.merge(
        pd.DataFrame(results),
        on="access_case_number",
        validate="one_to_one"
    )


def compare_access_organization(
    data,
    organization,
    value_column="difference_saisonniere",
    title="Variations après retrait de la référence saisonnière"
):
    """Compare une organisation aux autres pour l’indicateur choisi."""
    import matplotlib.pyplot as plt

    comparison = data.dropna(subset=[value_column]).copy()

    comparison["groupe"] = comparison["organization"].eq(
        organization
    ).map({
        True: "Organisation étudiée",
        False: "Autres organisations"
    })

    groups = ["Organisation étudiée", "Autres organisations"]

    summary = (
        comparison.groupby("groupe")
        .agg(
            nombre_acces=("access_case_number", "nunique"),
            nombre_sites=("site_code", "nunique"),
            variation_mediane=(value_column, "median")
        )
        .reindex(groups)
    )

    values = [
        comparison.loc[
            comparison["groupe"].eq(group), value_column
        ]
        for group in groups
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.boxplot(values, tick_labels=groups)

    for position, group_values in enumerate(values, start=1):
        ax.scatter(
            [position] * len(group_values),
            group_values,
            color="steelblue",
            alpha=0.5,
            s=20
        )

    ax.axhline(0, color="grey", linestyle="--")
    ax.set_ylabel("Variation comparée (observations / heure)")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()

    return summary


def compare_access_organizations_by_site(data, organization):
    """Compare les organisations avec une valeur par site et groupe."""
    import matplotlib.pyplot as plt

    data = data.dropna(subset=["difference_relative"]).copy()

    data["groupe"] = data["organization"].eq(organization).map({
        True: "Organisation étudiée",
        False: "Autres organisations"
    })

    site_summary = (
        data.groupby(["groupe", "site_code"])
        .agg(
            nombre_acces=("access_case_number", "nunique"),
            variation_mediane=("difference_relative", "median")
        )
        .reset_index()
    )

    groups = ["Organisation étudiée", "Autres organisations"]

    values = [
        site_summary.loc[
            site_summary["groupe"].eq(group),
            "variation_mediane"
        ]
        for group in groups
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.boxplot(values, tick_labels=groups)

    for position, group_values in enumerate(values, start=1):
        ax.scatter(
            [position] * len(group_values),
            group_values,
            color="steelblue",
            alpha=0.6
        )

    ax.axhline(0, color="grey", linestyle="--")
    ax.set_title("Variations relatives — une valeur par site et groupe")
    ax.set_ylabel("Variation médiane (observations / heure)")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    plt.show()

    summary = (
        site_summary.groupby("groupe")
        .agg(
            nombre_sites=("site_code", "nunique"),
            nombre_acces=("nombre_acces", "sum"),
            variation_mediane=("variation_mediane", "median")
        )
        .reindex(groups)
    )

    return summary


def plot_access_case_context(
        comparison, comparators, data, case_number, indicators=None):
    """Compare un site à ses comparateurs autour d’un accès."""
    import matplotlib.pyplot as plt

    event = comparison.loc[
        comparison["access_case_number"].eq(case_number)
    ].iloc[0]

    peers = comparators.loc[
        comparators["access_case_number"].eq(case_number),
        "sites_comparateurs"
    ].iloc[0]

    access_month = event["access_date"].to_period("M")

    observations = data.copy()
    observations["month"] = (
        observations["survey_start"].dt.to_period("M")
    )

    window = observations.loc[
        observations["month"].between(
            access_month - 6, access_month + 6
        )
    ]

    target = (
        window.loc[window["site_code"].eq(event["site_code"])]
        .sort_values("survey_start")
    )

    if indicators is None:
        indicators = {
            "bats_per_hour": "Activité (observations / heure)",
            "uptime_pct": "Disponibilité (%)",
            "acoustic_quality": "Qualité acoustique (score)"
        }

    peer_medians = (
        window.loc[window["site_code"].isin(peers)]
        .groupby("month")[list(indicators)]
        .median()
        .reindex(target["month"])
    )

    fig, axes = plt.subplots(
        len(indicators),
        1,
        figsize=(12, 3 * len(indicators)),
        sharex=True
    )
    for ax, (variable, label) in zip(axes, indicators.items()):
        ax.plot(
            target["survey_start"],
            target[variable],
            marker="o",
            label=event["site_code"]
        )

        ax.plot(
            target["survey_start"],
            peer_medians[variable].to_numpy(),
            linestyle="--",
            label="Médiane des comparateurs"
        )

        ax.axvline(
            event["access_date"],
            color="firebrick",
            linestyle=":",
            label="Début de l’accès"
        )

        ax.set_ylabel(label)
        ax.grid(alpha=0.3)

    axes[0].legend()
    axes[0].set_title(f"{case_number} — comparaison autour de l’accès")
    axes[-1].set_xlabel("Date")

    fig.tight_layout()
    plt.show()


def show_field_report(reports, document_id):
    """Affiche les informations et le texte d’un rapport."""
    report = reports.set_index("document_id").loc[document_id]

    print("Document :", document_id)
    print("Titre :", report["title"])
    print("Site :", report["site_code"])
    print("Date :", report["document_date"])
    print("Auteur :", report["author_name"])
    print("Organisation :", report["author_organization"])
    print("Enquête citée :", report["related_survey_id"])
    print("Appareil cité :", report["related_device_reference"])

    text = str(report["text"]).replace("\\r\\n", "\n")
    print("\nTexte du rapport :\n")
    print(text)


def prepare_report_texts(reports):
    """Prépare les textes en retirant leurs identifiants connus."""
    import re

    identifier_columns = [
        "document_id",
        "site_code",
        "related_survey_id",
        "related_device_reference"
    ]

    def clean_report(report):
        if pd.isna(report["text"]):
            return ""

        text = str(report["text"])

        # Retirer les identifiants avant de supprimer la ponctuation
        for column in identifier_columns:
            identifier = report[column]

            if pd.notna(identifier) and str(identifier).strip():
                text = re.sub(
                    re.escape(str(identifier).strip()),
                    " ",
                    text,
                    flags=re.IGNORECASE
                )

        text = text.lower()
        text = text.replace("\\r\\n", " ").replace("\\n", " ")
        text = re.sub(r"[^a-z\s]", " ", text)

        return re.sub(r"\s+", " ", text).strip()

    prepared = reports.copy()
    prepared["text_prepared"] = prepared.apply(
        clean_report, axis=1
    )

    return prepared


def plot_frequent_report_terms(reports, top_n=12):
    """Affiche les mots et bigrammes présents dans le plus de rapports."""
    import matplotlib.pyplot as plt
    from sklearn.feature_extraction.text import (
        CountVectorizer,
        ENGLISH_STOP_WORDS
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    results = {}

    for ax, size, title in zip(
        axes,
        [1, 2],
        ["Mots fréquents", "Expressions de deux mots"]
    ):
        vectorizer = CountVectorizer(
            ngram_range=(size, size),
            binary=True
        )

        matrix = vectorizer.fit_transform(reports["text_prepared"])
        terms = vectorizer.get_feature_names_out()
        counts = matrix.sum(axis=0).A1

        frequencies = pd.DataFrame({
            "terme": terms,
            "nombre_rapports": counts
        })

        # Filtrer après construction pour préserver les mots consécutifs
        keep = frequencies["terme"].apply(
            lambda term: all(
                word not in ENGLISH_STOP_WORDS
                for word in term.split()
            )
        )

        frequencies = (
            frequencies.loc[keep]
            .sort_values(
                ["nombre_rapports", "terme"],
                ascending=[False, True]
            )
            .head(top_n)
        )

        displayed = frequencies.iloc[::-1]

        ax.barh(
            displayed["terme"],
            displayed["nombre_rapports"],
            color="steelblue"
        )

        ax.bar_label(ax.containers[0], padding=3)
        ax.set_title(title)
        ax.set_xlabel("Nombre de rapports contenant le terme")
        ax.set_xlim(0, len(reports) + 2)
        ax.grid(axis="x", alpha=0.2)

        results[title] = frequencies

    fig.tight_layout()
    plt.show()

    return results


def extract_report_tfidf(reports, top_n=5):
    """Extrait les termes caractéristiques de chaque rapport."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_df=0.9,
        min_df=1,
        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(reports["text_prepared"])
    terms = vectorizer.get_feature_names_out()

    results = []

    for position, report in enumerate(reports.itertuples(index=False)):
        scores = matrix[position].toarray().ravel()

        selected = [
            index for index in scores.argsort()[::-1]
            if scores[index] > 0
        ][:top_n]

        results.append({
            "document_id": report.document_id,
            "title": report.title,
            "termes_caracteristiques": ", ".join(
                terms[index] for index in selected
            )
        })

    return matrix, vectorizer, pd.DataFrame(results)


def plot_report_similarity(reports, tfidf_matrix):
    """Représente les similarités cosinus entre tous les rapports."""
    import matplotlib.pyplot as plt
    from sklearn.metrics.pairwise import cosine_similarity

    identifiers = reports["document_id"].tolist()

    similarity = pd.DataFrame(
        cosine_similarity(tfidf_matrix),
        index=identifiers,
        columns=identifiers
    )

    fig, ax = plt.subplots(figsize=(12, 11))

    heatmap = ax.imshow(
        similarity.to_numpy(),
        cmap="YlGnBu",
        vmin=0,
        vmax=1
    )

    positions = range(len(identifiers))

    ax.set_xticks(positions)
    ax.set_xticklabels(identifiers, rotation=90, fontsize=7)
    ax.set_yticks(positions)
    ax.set_yticklabels(identifiers, fontsize=7)

    ax.set_title("Similarité cosinus entre les rapports — TF-IDF")
    fig.colorbar(
        heatmap,
        ax=ax,
        label="Similarité cosinus",
        shrink=0.8
    )

    fig.tight_layout()
    plt.show()

    return similarity


def compare_report_references(reports, surveys, operations):
    """Rapproche tous les rapports de leurs enquêtes et appareils."""
    survey_columns = [
        "survey_id",
        "site_code",
        "survey_start",
        "bats_per_hour"
    ]

    survey_data = surveys[survey_columns].rename(columns={
        "survey_id": "related_survey_id",
        "site_code": "site_releve"
    })

    comparison = reports.merge(
        survey_data,
        on="related_survey_id",
        how="left",
        validate="many_to_one"
    )

    comparison["enquete_retrouvee"] = (
        comparison["survey_start"].notna()
    )

    comparison["meme_site"] = (
        comparison["site_code"].eq(comparison["site_releve"])
        .where(comparison["enquete_retrouvee"])
    )

    comparison["rapport_avant_releve"] = (
        comparison["document_date"].dt.normalize()
        .lt(comparison["survey_start"].dt.normalize())
        .where(comparison["enquete_retrouvee"])
    )

    comparison["month"] = (
        comparison["survey_start"].dt.to_period("M")
    )

    device_data = operations.copy()
    device_data["month"] = (
        device_data["operation_start"].dt.to_period("M")
    )

    device_data = device_data.rename(columns={
        "device_reference": "related_device_reference"
    })

    comparison = comparison.merge(
        device_data[
            [
                "site_code",
                "related_device_reference",
                "month",
                "device_operation_id",
                "uptime_pct",
                "acoustic_quality",
                "fault_code"
            ]
        ],
        on=["site_code", "related_device_reference", "month"],
        how="left",
        validate="many_to_one"
    )

    comparison["appareil_mois_retrouve"] = (
        comparison["device_operation_id"].notna()
    )

    return comparison


def summarize_report_measurements(reports, observations):
    """Compare les mesures citées à une référence saisonnière locale."""
    data = observations.copy()
    data["calendar_month"] = data["survey_start"].dt.month

    results = []

    for report in reports.itertuples(index=False):
        observed = data.loc[
            data["survey_id"].eq(report.related_survey_id)
        ].iloc[0]

        reference = data.loc[
            data["site_code"].eq(observed["site_code"])
            & data["calendar_month"].eq(observed["calendar_month"])
            & data["survey_id"].ne(report.related_survey_id)
        ]

        usual_activity = reference["bats_per_hour"].median()
        usual_rainfall = reference["rainfall_mm"].median()

        results.append({
            "document_id": report.document_id,
            "site_code": observed["site_code"],
            "mois_enquete": observed["survey_start"].to_period("M"),
            "activite_observee": observed["bats_per_hour"],
            "activite_reference": usual_activity,
            "ecart_activite": (
                observed["bats_per_hour"] - usual_activity
            ),
            "pluie_mm": observed["rainfall_mm"],
            "pluie_reference_mm": usual_rainfall,
            "ecart_pluie_mm": (
                observed["rainfall_mm"] - usual_rainfall
            )
        })

    return pd.DataFrame(results)


def plot_site_access_graph(accesses):
    """Construit un graphe biparti reliant sites et accès étudiables."""
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    events = accesses.sort_values(
        ["site_code", "access_date"]
    ).reset_index(drop=True)

    graph = nx.Graph()
    positions = {}
    site_positions = {}

    for index, event in enumerate(events.itertuples(index=False)):
        site_node = ("site", event.site_code)
        access_node = ("access", event.access_case_number)

        graph.add_node(
            site_node,
            type="site",
            label=event.site_code
        )
        graph.add_node(
            access_node,
            type="access",
            label=event.access_case_number,
            date=event.access_date,
            organization=event.organization
        )
        graph.add_edge(site_node, access_node)

        y = len(events) - index
        positions[access_node] = (1, y)
        site_positions.setdefault(site_node, []).append(y)

    for site_node, values in site_positions.items():
        positions[site_node] = (0, sum(values) / len(values))

    site_nodes = list(site_positions)
    access_nodes = [
        node for node in graph if graph.nodes[node]["type"] == "access"
    ]

    fig, ax = plt.subplots(
        figsize=(12, max(6, 0.28 * len(events)))
    )

    nx.draw_networkx_edges(
        graph, positions,
        ax=ax, edge_color="lightgrey", width=1.2
    )

    nx.draw_networkx_nodes(
        graph, positions, nodelist=site_nodes,
        node_color="steelblue", node_size=65, ax=ax
    )

    nx.draw_networkx_nodes(
        graph, positions, nodelist=access_nodes,
        node_color="darkorange", node_size=45, ax=ax
    )

    for node, (x, y) in positions.items():
        is_site = graph.nodes[node]["type"] == "site"

        ax.text(
            x - 0.04 if is_site else x + 0.04,
            y,
            graph.nodes[node]["label"],
            ha="right" if is_site else "left",
            va="center",
            fontsize=8
        )

    legend = [
        Line2D(
            [], [], marker="o", linestyle="",
            color="steelblue", label="Site"
        ),
        Line2D(
            [], [], marker="o", linestyle="",
            color="darkorange", label="Accès"
        )
    ]

    ax.legend(handles=legend, loc="upper center", ncol=2)
    ax.set_title("Liens entre les sites et les accès étudiables")
    ax.set_xlim(-0.4, 1.9)
    ax.set_ylim(0, len(events) + 3)
    ax.axis("off")

    fig.tight_layout()
    plt.show()

    return graph
