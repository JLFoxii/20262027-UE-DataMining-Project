"""Étape 2 : créer des colonnes numériques traçables dans interim.

Entrée : CSV dédupliqués data/interim/logistics/.
Sortie : CSV data/interim/logistics_numeric/ avec les colonnes sources conservées
et de nouvelles colonnes <nom>_numeric (décimales avec point, sans unité).
La devise et la colonne d'unité séparée restent inchangées.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation

import pandas as pd

from build_data import FILES, INTERIM, ROOT, sha256

NUMERIC_INTERIM = ROOT / "data" / "interim" / "logistics_numeric"


# Les colonnes sélectionnées sont les seules converties à ce stade.
# Une valeur comportant une unité doit correspondre exactement à la colonne
# d'unité déjà présente dans le CSV.
NUMERIC_FIELDS = {
    "purchase_order_lines.csv": (
        "ordered_unit",
        ("ordered_quantity", "unit_price"),
    ),
    "goods_receipts.csv": ("received_unit", ("received_quantity",)),
    "shipments.csv": ("declared_unit", ("declared_quantity",)),
    "inventory_month_end.csv": (
        "unit",
        (
            "opening_stock",
            "received_quantity",
            "outgoing_quantity",
            "documented_internal_use",
            "documented_waste",
            "closing_stock",
        ),
    ),
    "inventory_adjustments.csv": ("unit", ("adjustment_quantity",)),
}

NUMERIC_PATTERN = re.compile(
    r"^([+-]?\d+(?:[.,]\d+)?)(?:\s+([A-Za-z_][\w-]*))?$"
)


def normalize(value: str, expected_unit: str | None, *, field: str) -> tuple[str, str]:
    """Renvoie valeur canonique et type de correction ; refuse toute ambiguïté."""
    raw = value.strip()
    match = NUMERIC_PATTERN.fullmatch(raw)
    if match is None:
        raise ValueError(f"{field} : valeur numérique non reconnue {value!r}")

    number, embedded_unit = match.groups()
    if embedded_unit is not None:
        if expected_unit is None:
            raise ValueError(f"{field} : unité inattendue dans {value!r}")
        if embedded_unit != expected_unit.strip():
            raise ValueError(
                f"{field} : unité {embedded_unit!r} différente de {expected_unit!r}"
            )
    canonical = number.replace(",", ".")
    try:
        Decimal(canonical)
    except InvalidOperation as exc:
        raise ValueError(f"{field} : nombre non décimal {value!r}") from exc

    if embedded_unit is not None:
        return canonical, "avec_unite"
    if "," in number:
        return canonical, "virgule"
    return canonical, "standard"


def build_processed() -> list[dict[str, object]]:
    """Produit l'étape numérique intermédiaire, sans toucher à processed."""
    NUMERIC_INTERIM.mkdir(parents=True, exist_ok=True)
    reports: list[dict[str, object]] = []

    for file in FILES:
        interim_path = INTERIM / file
        if not interim_path.is_file():
            raise FileNotFoundError(f"Interim manquant : {interim_path}")
        df = pd.read_csv(interim_path, dtype=str, keep_default_na=False)
        original_columns = list(df.columns)
        breakdown = {}
        if file in NUMERIC_FIELDS:
            unit_column, columns = NUMERIC_FIELDS[file]
            for column in columns:
                normalized = [
                    normalize(
                        original_value,
                        # Le prix n'a pas d'unité de quantité ; la devise est
                        # déjà portée par la colonne 'currency'.
                        None if column == "unit_price" else unit_value,
                        field=f"{file}:{column}:ligne {i + 2}",
                    )
                    for i, (original_value, unit_value) in enumerate(
                        zip(df[column], df[unit_column], strict=True)
                    )
                ]
                df[f"{column}_numeric"] = [value for value, _ in normalized]
                breakdown[column] = {
                    "standard": sum(kind == "standard" for _, kind in normalized),
                    "virgule_decimale": sum(kind == "virgule" for _, kind in normalized),
                    "nombre_avec_unite": sum(kind == "avec_unite" for _, kind in normalized),
                }

        # Une copie des colonnes d'origine reste identique à interim.
        source = pd.read_csv(interim_path, dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(df[original_columns], source)
        output = NUMERIC_INTERIM / file
        df.to_csv(output, index=False)
        written = pd.read_csv(output, dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(written, df)
        pd.testing.assert_frame_equal(written[original_columns], source)
        assert len(df) == len(source)

        reports.append(
            {
                "fichier": file,
                "lignes": len(df),
                "colonnes_numeriques_ajoutees": len(breakdown),
                "virgules_decimales": sum(x["virgule_decimale"] for x in breakdown.values()),
                "nombres_avec_unite": sum(x["nombre_avec_unite"] for x in breakdown.values()),
                "details": breakdown,
                "interim_sha256": sha256(interim_path),
                "numeric_interim_sha256": sha256(output),
            }
        )

    manifest = {
        "transformation": "ajout de colonnes *_numeric ; colonnes originales conservées",
        "source": "data/interim/logistics/",
        "destination": "data/interim/logistics_numeric/",
        "unites": "aucune conversion d'unités",
        "devises": "aucune conversion de devises",
        "fichiers": reports,
    }
    (NUMERIC_INTERIM / "numeric_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return reports


if __name__ == "__main__":
    reports = build_processed()
    for item in reports:
        print(
            f'{item["fichier"]}: {item["lignes"]} lignes, '
            f'{item["colonnes_numeriques_ajoutees"]} colonnes numériques ajoutées'
        )
    print("Virgules décimales traitées :", sum(int(r["virgules_decimales"]) for r in reports))
    print("Nombres avec unité traités :", sum(int(r["nombres_avec_unite"]) for r in reports))
    print("Aucune colonne d'origine ni aucun fichier raw/interim modifié.")
