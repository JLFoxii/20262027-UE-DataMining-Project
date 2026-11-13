"""Étape 2 : dates et libellés, après normalisation numérique.

Lit data/interim/logistics_numeric/ et génère data/processed/logistics/.
Chaque colonne d'origine (ainsi que les colonnes *_numeric) est préservée.
Les dates JJ/MM/AAAA réellement ambiguës restent non résolues et sont
signalées : aucune interprétation n'est choisie par défaut.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

import pandas as pd

from build_data import FILES, PROCESSED, sha256
from normalize_numeric import NUMERIC_INTERIM


DATE_COLUMNS = {
    "purchase_order_lines.csv": ("order_date", "requested_delivery_date"),
    "goods_receipts.csv": ("receipt_date",),
    "shipments.csv": ("dispatch_time", "arrival_time"),
    "inventory_month_end.csv": ("reporting_month",),
    "inventory_adjustments.csv": ("adjustment_date",),
    "erp_business_partners.csv": ("onboarding_date",),
    "erp_facilities.csv": ("opening_date",),
}

# Ces sept colonnes présentent 15 groupes de libellés variant seulement
# par la casse dans le jeu actuel. Les autres catégories restent inchangées.
CATEGORY_COLUMNS = {
    "purchase_order_lines.csv": ("item_category",),
    "goods_receipts.csv": ("receipt_status",),
    "shipments.csv": ("shipment_status", "temperature_control_class"),
    "inventory_month_end.csv": ("inventory_status",),
    "inventory_adjustments.csv": ("adjustment_reason",),
    "erp_business_partners.csv": ("partner_role",),
}

ENGLISH_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_date(value: str) -> tuple[str, str, tuple[str, str] | None]:
    """Renvoie (ISO, statut, candidats), sans supposer l'ordre du jour et du mois."""
    raw = value.strip()
    if not raw:
        return "", "missing", None

    # Les dates déjà ISO sont interprétées strictement (pas de dayfirst global).
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date().isoformat(), "iso", None
        except ValueError as exc:
            raise ValueError(f"Date ISO impossible : {raw!r}") from exc
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", raw):
        try:
            return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S").isoformat(), "iso", None
        except ValueError as exc:
            raise ValueError(f"Date/heure ISO impossible : {raw!r}") from exc

    # AAAA/MM/JJ et AAAA/MM/JJ HH:MM:SS sont non ambigus par construction.
    if re.fullmatch(r"\d{4}/\d{2}/\d{2}(?: \d{2}:\d{2}:\d{2})?", raw):
        fmt = "%Y/%m/%d %H:%M:%S" if " " in raw else "%Y/%m/%d"
        date = datetime.strptime(raw, fmt)
        return (date.isoformat() if " " in raw else date.date().isoformat()), "reformatted", None

    # JJ-Mon-AAAA avec mois anglais explicite, indépendant de la locale du Mac.
    month_text = re.fullmatch(
        r"(\d{1,2})-([A-Za-z]{3})-(\d{4})(?: (\d{2}:\d{2}:\d{2}))?", raw
    )
    if month_text:
        day, month_name, year, time = month_text.groups()
        month = ENGLISH_MONTHS.get(month_name.casefold())
        if month is None:
            raise ValueError(f"Mois anglais inconnu : {raw!r}")
        iso_candidate = f"{year}-{month:02d}-{int(day):02d}"
        if time:
            return datetime.fromisoformat(f"{iso_candidate}T{time}").isoformat(), "reformatted", None
        return datetime.fromisoformat(iso_candidate).date().isoformat(), "reformatted", None

    # JJ/MM/AAAA : lorsque les deux premières composantes peuvent être le mois,
    # ne pas inventer un ordre. On garde les deux scénarios pour revue humaine.
    slash = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})(?: (\d{2}:\d{2}:\d{2}))?", raw)
    if slash:
        first, second, year, time = slash.groups()
        first_int, second_int = int(first), int(second)
        try:
            day_first_date = datetime(int(year), second_int, first_int)
        except ValueError as exc:
            raise ValueError(f"JJ/MM/AAAA impossible : {raw!r}") from exc
        day_first = day_first_date.date().isoformat()
        if time:
            day_first = datetime.fromisoformat(day_first + "T" + time).isoformat()

        if first_int <= 12 and second_int <= 12 and first_int != second_int:
            month_first_date = datetime(int(year), first_int, second_int)
            month_first = month_first_date.date().isoformat()
            if time:
                month_first = datetime.fromisoformat(month_first + "T" + time).isoformat()
            return "", "ambiguous_day_month", (day_first, month_first)
        return day_first, "reformatted", None

    raise ValueError(f"Format de date non reconnu : {raw!r}")


def normalize_processed() -> dict[str, object]:
    """Reconstruit processed à partir de l'étape numérique, sans toucher aux sources."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    result: list[dict[str, object]] = []
    ambiguous_dates: list[dict[str, object]] = []

    for file in FILES:
        source = NUMERIC_INTERIM / file
        if not source.is_file():
            raise FileNotFoundError(f"Étape numérique absente : {source}")
        df = pd.read_csv(source, dtype=str, keep_default_na=False)
        before_columns = list(df.columns)
        date_count = {"iso": 0, "reformatted": 0, "missing": 0, "ambiguous_day_month": 0}
        category_summary: list[dict[str, object]] = []

        for column in DATE_COLUMNS.get(file, ()):
            parsed = [parse_date(value) for value in df[column]]
            df[f"{column}_normalized"] = [iso for iso, _, _ in parsed]
            df[f"{column}_parse_status"] = [status for _, status, _ in parsed]
            for idx, (iso, status, candidates) in enumerate(parsed):
                date_count[status] += 1
                if candidates:
                    ambiguous_dates.append({
                        "fichier": file,
                        "colonne": column,
                        "ligne_interim": idx + 2,
                        "valeur_brute": df.at[idx, column],
                        "candidat_JJ_MM": candidates[0],
                        "candidat_MM_JJ": candidates[1],
                    })

        for column in CATEGORY_COLUMNS.get(file, ()):
            raw = df[column]
            normalized = raw.str.strip().str.casefold()
            df[f"{column}_normalized"] = normalized
            # Nombre de valeurs canoniques ayant plusieurs écritures originales.
            variants = pd.DataFrame({"raw": raw, "normalized": normalized})
            variant_groups = int((variants.groupby("normalized")["raw"].nunique() > 1).sum())
            category_summary.append({
                "colonne": column,
                "modalites_originales": int(raw.nunique()),
                "modalites_normalisees": int(normalized.nunique()),
                "groupes_variants_casse": variant_groups,
            })

        output = PROCESSED / file
        df.to_csv(output, index=False)
        written = pd.read_csv(output, dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(written, df)
        pd.testing.assert_frame_equal(written[before_columns], pd.read_csv(source, dtype=str, keep_default_na=False))
        result.append({
            "fichier": file,
            "lignes": len(df),
            "dates": date_count,
            "categories": category_summary,
            "numeric_interim_sha256": sha256(source),
            "processed_sha256": sha256(output),
        })

    manifest = {
        "transformation": "dates explicites, dates ambiguës signalées, catégories en casse canonique",
        "source": "data/interim/logistics_numeric/",
        "destination": "data/processed/logistics/",
        "regle_ambiguites": "JJ/MM/AAAA ambigu : valeur normalisée vide, valeur brute et deux candidats conservés",
        "fichiers": result,
        "dates_ambigues": ambiguous_dates,
    }
    (PROCESSED / "processed_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    manifest = normalize_processed()
    for item in manifest["fichiers"]:
        dates = item["dates"]
        cases = sum(x["groupes_variants_casse"] for x in item["categories"])
        print(f'{item["fichier"]}: {dates["reformatted"]} dates reformatées, '
              f'{dates["ambiguous_day_month"]} ambiguës, {cases} groupes de casse')
    print(f'Dates ambiguës non converties : {len(manifest["dates_ambigues"])}')
    print("Aucune donnée officielle, raw ou interim modifiée.")
