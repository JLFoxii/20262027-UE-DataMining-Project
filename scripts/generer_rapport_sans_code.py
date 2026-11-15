#!/usr/bin/env python3
"""Reconstruit les tableaux et figures du rapport collectif *sans code visible*.

Les calculs sont isolés dans scripts/calculs_rapport_collectif.py ; le notebook
final contient exclusivement du Markdown et des figures intégrées, sans dépendre
d'un ancien notebook de brouillon. Les paragraphes rédigés dans le rapport ne
sont jamais remplacés par ce programme ; seules ses cellules de résultats,
identifiées par rapport_source_cell, sont régénérées.

Exécution depuis n'importe quel dossier (dans l'environnement du projet) :
    uv run python scripts/generer_rapport_sans_code.py --reexecute
Vérification sans recalcul :
    uv run python scripts/generer_rapport_sans_code.py --check
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import os
import re

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parent.parent
CODE_SOURCE = ROOT / "scripts/calculs_rapport_collectif.py"
DESTINATION = ROOT / "Rapport_collectif_Data_Mining_M2DS_2026_2027.ipynb"

FIGURE_CAPTIONS = {
    7: "Étapes enregistrées dans les dossiers d'accès",
    11: "Organisations reliées aux dirigeants par les mandats déclarés",
    16: "PAT-31065 : périodicités cardiaques estimées par autocorrélation",
    20: "Variations écologiques après accès, avec correction saisonnière",
    24: "Réceptions partielles : répartition des écarts de quantité",
    29: "Présence des termes du narratif dans les quatre corpus textuels",
    34: "Répartition annuelle des correspondances Horizon–Meridian",
}
TABLE_CAPTIONS = {
    6: ["Volumes et durées des dossiers"],
    10: ["Licence médicale retrouvée dans les registres"],
    11: ["Organisations ayant le plus de liens déclarés"],
    15: ["Périodes estimées pour les deux enregistrements cardiaques"],
    19: ["Comparaison des accès après correction saisonnière"],
    23: ["Rapprochement des commandes et des réceptions"],
    25: ["Principaux flux entre partenaires logistiques"],
    28: ["Répartition des documents par corpus", "Documents pivots de l'enquête"],
    29: ["Termes du narratif retrouvés dans les documents"],
    33: ["Exemples des correspondances d'accès et d'expédition"],
    35: ["Comparaison avec les 36 autres accès terminés"],
    42: ["Vérification des cinq références ACC dans leur table d'origine"],
}

class TableParser(HTMLParser):
    """Extraction minimale de tableaux HTML pandas, sans dépendance lxml."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.section = None
        self.row = None
        self.value = None
        self.head = []
        self.body = []

    def handle_starttag(self, tag, attrs):
        if tag == "table" and not self.in_table:
            self.in_table = True
        if not self.in_table:
            return
        if tag in ("thead", "tbody"):
            self.section = tag
        elif tag == "tr":
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            self.value = []

    def handle_data(self, data):
        if self.value is not None:
            self.value.append(data)

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag in ("th", "td") and self.value is not None:
            self.row.append("".join(self.value).strip())
            self.value = None
        elif tag == "tr" and self.row is not None:
            (self.head if self.section == "thead" else self.body).append(self.row)
            self.row = None
        elif tag in ("thead", "tbody"):
            self.section = None
        elif tag == "table":
            self.in_table = False


def markdown_table(html: str) -> str:
    parser = TableParser()
    parser.feed(html)
    if not parser.head or not parser.body:
        raise ValueError("Un tableau HTML pandas n'a pas pu être converti.")
    headings = parser.head[0].copy()
    # Les DataFrames à index nommé ont une seconde rangée contenant le nom
    # de l'index. Sans index nommé, le premier th vide correspond aux numéros
    # de ligne que nous supprimons (ils ne font pas partie des données).
    named_index = next((row[0] for row in parser.head[1:] if row and row[0]), "")
    if headings and not headings[0]:
        if named_index:
            headings[0] = named_index
            rows = parser.body
        else:
            headings = headings[1:]
            rows = [row[1:] for row in parser.body]
    else:
        rows = parser.body

    def clean(cell):
        return re.sub(r"\s+", " ", str(cell)).strip().replace("|", "\\|").replace("\n", " ")

    headings = [clean(h) for h in headings]
    rows = [[clean(x) for x in row] for row in rows]
    if not headings or any(len(row) != len(headings) for row in rows):
        raise ValueError(f"Tableau incohérent : colonnes={len(headings)}, lignes={[len(r) for r in rows]}")
    result = ["| " + " | ".join(headings) + " |",
              "| " + " | ".join(["---"] * len(headings)) + " |"]
    result.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(result)


def simplify_stream(text: str) -> str:
    """Retire le chemin personnel et reformate les sorties en courtes lignes."""
    parts = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("Données du dépôt :") or line.startswith("Aucune source CSV ne sera"):
            continue
        line = line.replace("[np.float64(6.0)]", "6 heures")
        parts.append(line)
    return "  \n".join(parts)


def convert_output_cell(source_index: int, code_cell) -> nbformat.NotebookNode | None:
    blocks = []
    attachments = {}
    table_count = 0
    image_count = 0
    for output in code_cell.get("outputs", []):
        if output.output_type == "error":
            raise RuntimeError(f"Erreur dans une cellule source {source_index} : {output.ename}: {output.evalue}")
        if output.output_type == "stream":
            s = simplify_stream(output.get("text", ""))
            if s:
                blocks.append(s)
            continue
        if output.output_type not in ("display_data", "execute_result"):
            continue
        data = output.get("data", {})
        if "text/html" in data:
            names = TABLE_CAPTIONS.get(source_index, [])
            caption = names[table_count] if table_count < len(names) else "Résultat du calcul"
            blocks.append(f"**Tableau — {caption}**\n\n{markdown_table(data['text/html'])}")
            table_count += 1
        if "image/png" in data:
            png_name = f"figure-{source_index}-{image_count}.png"
            alt = FIGURE_CAPTIONS.get(source_index, "Figure issue des analyses")
            # Le PNG est encodé dans la cellule Markdown elle-même.
            attachments[png_name] = {"image/png": data["image/png"]}
            blocks.append(f"**Figure — {alt}**\n\n![{alt}](attachment:{png_name})")
            image_count += 1
    if not blocks:
        return None
    cell = nbformat.v4.new_markdown_cell("\n\n".join(blocks))
    if attachments:
        cell.attachments = attachments
    return cell



def read_calculation_cells():
    """Décompose le fichier Python en cellules indépendantes mais séquentielles."""
    if not CODE_SOURCE.is_file():
        raise FileNotFoundError(CODE_SOURCE)
    content=CODE_SOURCE.read_text(encoding="utf-8")
    blocks=re.split(r"(?m)^# %% source-cell=(\d+)\s*$",content)
    if len(blocks)<3 or (len(blocks)-1)%2:
        raise ValueError("Marqueurs de cellules manquants ou mal formés")
    indices=[]
    cells=[]
    for i in range(1,len(blocks),2):
        ix=int(blocks[i])
        text=blocks[i+1].strip()
        if ix in indices or not text:
            raise ValueError(f"Cellule source dupliquée ou vide : {ix}")
        indices.append(ix)
        cells.append(nbformat.v4.new_code_cell(text))
    assert len(indices)==19, f"Attendu 19 blocs Python, reçu {len(indices)}"
    return indices, cells


def validate_report(report):
    nbformat.validate(report)
    if any(cell.cell_type!="markdown" for cell in report.cells):
        raise ValueError("Le rapport doit être 100 % Markdown")
    images=sum(len(c.get("attachments",{})) for c in report.cells)
    tables=sum(c.source.count("**Tableau —") for c in report.cells)
    if images!=7 or tables!=13:
        raise ValueError(f"Rapport incomplet : {images} figures et {tables} tableaux (attendus 7 et 13)")
    for c in report.cells:
        for name in re.findall(r"attachment:([^)]*)",c.source):
            if name not in c.get("attachments",{}):
                raise ValueError(f"Pièce jointe manquante : {name}")
    return images,tables


def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("--check",action="store_true",help="Contrôler sans modifier ni exécuter")
    args.add_argument("--reexecute",action="store_true",help="Recalculer et remplacer uniquement les cellules de résultats (défaut)")
    opt=args.parse_args()
    if not DESTINATION.is_file():
        raise FileNotFoundError(DESTINATION)
    report=nbformat.read(DESTINATION,as_version=4)
    before=validate_report(report)
    if opt.check:
        print(f"Vérification OK : {len(report.cells)} cellules Markdown, {before[0]} figures, {before[1]} tableaux")
        return

    indices,cells=read_calculation_cells()
    run_nb=nbformat.v4.new_notebook(cells=cells)
    run_nb.metadata.kernelspec={"name":"python3","language":"python","display_name":"Python 3"}
    print("Exécution des 19 blocs de calculs sur les CSV du dépôt…",flush=True)
    executed,_=ExecutePreprocessor(timeout=240,kernel_name="python3",allow_errors=False).preprocess(
        run_nb,{"metadata":{"path":str(ROOT)}}
    )
    new_outputs={}
    for index,cell in zip(indices,executed.cells):
        converted=convert_output_cell(index,cell)
        if converted is not None:
            new_outputs[index]=converted
    used=set()
    for cell in report.cells:
        if "rapport_source_cell" not in cell.metadata:
            continue
        index=int(cell.metadata["rapport_source_cell"])
        if index not in new_outputs:
            raise ValueError(f"Résultat absent après calcul : bloc {index}")
        converted=new_outputs[index]
        cell.source=converted.source
        if converted.get("attachments"):
            cell.attachments=converted.attachments
        else:
            cell.pop("attachments",None)
        used.add(index)
    if used!=set(new_outputs):
        raise ValueError(f"Cellules générées incohérentes : attendues {set(new_outputs)}, trouvées {used}")
    figures,tables=validate_report(report)
    tmp=DESTINATION.with_suffix('.ipynb.tmp')
    try:
        nbformat.write(report,tmp)
        os.replace(tmp,DESTINATION)
    finally:
        if tmp.exists():tmp.unlink()
    print(f"Régénération réussie : {DESTINATION.name} — {len(report.cells)} cellules Markdown, {figures} figures, {tables} tableaux, aucun code visible")


if __name__=="__main__":
    main()
