"""Préparation reproductible des CSV logistiques (étape 2 : doublons exacts).

Les sources officielles data/logistics/ restent intactes.
raw = copie byte-à-byte ; interim = mêmes lignes, moins les doublons exacts.
processed est réservé aux étapes ultérieures et n'est jamais modifié ici.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "logistics"
RAW = ROOT / "data" / "raw" / "logistics"
INTERIM = ROOT / "data" / "interim" / "logistics"
PROCESSED = ROOT / "data" / "processed" / "logistics"

FILES = (
    "purchase_order_lines.csv",
    "goods_receipts.csv",
    "shipments.csv",
    "inventory_month_end.csv",
    "inventory_adjustments.csv",
    "erp_business_partners.csv",
    "erp_facilities.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build() -> list[dict[str, object]]:
    """Crée ou vérifie raw puis génère les CSV interim sans changer les sources."""
    for directory in (RAW, INTERIM, PROCESSED):
        directory.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []
    for name in FILES:
        source = SOURCE / name
        raw = RAW / name
        interim = INTERIM / name
        if not source.is_file():
            raise FileNotFoundError(f"CSV officiel manquant : {source}")

        source_hash = sha256(source)
        if raw.exists():
            if sha256(raw) != source_hash:
                raise ValueError(
                    f"Copie raw différente de la source : {raw}. "
                    "Arrêt pour ne pas écraser un historique existant."
                )
        else:
            shutil.copy2(source, raw)
        assert sha256(raw) == source_hash, f"Copie raw non conforme : {name}"

        # dtype=str et keep_default_na=False préservent les valeurs textuelles
        # (dont unités, virgules décimales et cellules vides) à cette étape.
        original = pd.read_csv(raw, dtype=str, keep_default_na=False)
        cleaned = original.drop_duplicates(keep="first").reset_index(drop=True)
        cleaned.to_csv(interim, index=False)

        verification = pd.read_csv(interim, dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(cleaned, verification)
        if verification.duplicated().any():
            raise AssertionError(f"Doublons exacts encore présents : {name}")

        results.append(
            {
                "fichier": name,
                "lignes_raw": len(original),
                "doublons_retires": len(original) - len(cleaned),
                "lignes_interim": len(cleaned),
                "source_sha256": source_hash,
                "raw_sha256": sha256(raw),
                "interim_sha256": sha256(interim),
            }
        )

    (INTERIM / "manifest.json").write_text(
        json.dumps(
            {
                "operation": "suppression des doublons exacts seulement",
                "source_officielle": "data/logistics/",
                "raw": "data/raw/logistics/",
                "interim": "data/interim/logistics/",
                "processed": "data/processed/logistics/ (réservé aux étapes futures)",
                "fichiers": results,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return results


if __name__ == "__main__":
    report = build()
    for row in report:
        print(
            f'{row["fichier"]}: {row["lignes_raw"]} -> '
            f'{row["lignes_interim"]} '
            f'(doublons exacts retirés : {row["doublons_retires"]})'
        )
    print("Total des doublons retirés :", sum(int(r["doublons_retires"]) for r in report))
    print("Sources officielles préservées ; processed non modifié.")
