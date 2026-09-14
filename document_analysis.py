"""Reusable helpers for the four textual document sources.

The module is deliberately independent from the notebook.  It loads the CSV
files, harmonises their metadata, prepares text columns, and exposes small
functions for filtering, sorting, quality checks and text-frequency analysis.

Typical notebook usage::

    from document_analysis import (
        set_analysis_folder,
        load_active_documents,
        load_all_documents,
        document_summary,
        filter_documents,
        sort_documents,
        spearman_correlation,
        word_frequencies,
    )

    set_analysis_folder("public_records")
    documents = load_active_documents()
    recent = sort_documents(documents, by="document_date", ascending=False)
    restricted = filter_documents(recent, access_status="restricted")
    correlations = spearman_correlation(documents)
    top_words = word_frequencies(documents)

Pandas is imported lazily so that the module can still be inspected or
documented in an environment where the notebook dependencies are not yet
installed.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import unicodedata
from typing import Iterable, Mapping, Sequence

try:
    import pandas as pd
except ImportError:  # pragma: no cover - exercised only before setup
    pd = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parent

# The keys are stable names to use in a notebook.  The paths are relative to
# the project root, which makes the functions work from any current folder.
DOCUMENT_FILES: Mapping[str, Path] = {
    "public_investigative": Path(
        "data/public_records/public_and_investigative_documents.csv"
    ),
    "institutional_memos": Path(
        "data/public_records/institutional_memos.csv"
    ),
    "clinical_notes": Path("data/health/clinical_notes.csv"),
    "environmental_reports": Path(
        "data/ecology/environmental_field_reports.csv"
    ),
}

DOCUMENT_FAMILIES: Mapping[str, str] = {
    "public_investigative": "public_records",
    "institutional_memos": "public_records",
    "clinical_notes": "health",
    "environmental_reports": "ecology",
}

# A notebook can switch between these scopes without rewriting its loading
# code.  ``all`` loads the four textual sources; a folder loads the document
# sources belonging to that data family.
ANALYSIS_FOLDERS: Mapping[str, tuple[str, ...]] = {
    "all": tuple(DOCUMENT_FILES),
    "public_records": ("public_investigative", "institutional_memos"),
    "health": ("clinical_notes",),
    "ecology": ("environmental_reports",),
}

FOLDER_ALIASES: Mapping[str, str] = {
    "public": "public_records",
    "medical": "health",
    "ecological": "ecology",
    "all_documents": "all",
}

# Global notebook switcher.  Use ``set_analysis_folder`` rather than
# assigning this variable from an imported namespace.
ACTIVE_ANALYSIS_FOLDER = "all"

# The data is in English.  The set is intentionally modest and can be
# replaced by the caller when a different language or stop-word policy is
# needed.
DEFAULT_ENGLISH_STOPWORDS = frozenset(
    {
        "a",
        "about",
        "after",
        "again",
        "all",
        "also",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "before",
        "being",
        "between",
        "both",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "for",
        "from",
        "further",
        "had",
        "has",
        "have",
        "he",
        "her",
        "here",
        "hers",
        "him",
        "his",
        "how",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "just",
        "may",
        "more",
        "most",
        "must",
        "no",
        "not",
        "of",
        "on",
        "once",
        "only",
        "or",
        "other",
        "our",
        "out",
        "over",
        "same",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "under",
        "until",
        "up",
        "very",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "whom",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
    }
)

TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)


def _require_pandas() -> None:
    """Raise a useful error when the notebook environment is not ready."""

    if pd is None:
        raise ImportError(
            "document_analysis nécessite pandas. "
            "Installe pandas dans l'environnement du notebook avant de charger les données."
        )


def _as_list(values: str | Iterable[str] | None) -> list[str] | None:
    if values is None:
        return None
    if isinstance(values, str):
        return [values]
    return list(values)


def normalize_text(value: object) -> str:
    """Normalize a text value without changing its meaning.

    Newlines and repeated spaces are collapsed because the source documents
    contain long multiline fields.  The original ``text`` column is kept by
    :func:`prepare_documents`; this function is only used to create analysis
    columns.
    """

    if value is None:
        return ""
    if pd is not None:
        try:
            if bool(pd.isna(value)):
                return ""
        except (TypeError, ValueError):
            pass

    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())


def tokenize_text(
    text: object,
    *,
    lowercase: bool = True,
    min_length: int = 2,
    remove_numbers: bool = True,
) -> list[str]:
    """Return simple Unicode word tokens suitable for exploratory analysis."""

    normalized = normalize_text(text)
    if lowercase:
        normalized = normalized.lower()

    tokens = TOKEN_PATTERN.findall(normalized)
    if remove_numbers:
        tokens = [token for token in tokens if not token.isnumeric()]
    return [token for token in tokens if len(token) >= min_length]


def _clean_string_columns(frame: "pd.DataFrame") -> "pd.DataFrame":
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        frame[column] = (
            frame[column]
            .astype("string")
            .str.replace("\u00a0", " ", regex=False)
            .str.strip()
        )
    return frame


def _coalesce_columns(frame: "pd.DataFrame", columns: Sequence[str]) -> "pd.Series":
    available = [column for column in columns if column in frame.columns]
    if not available:
        return pd.Series("", index=frame.index, dtype="string")

    values = frame[available].astype("string").replace("", pd.NA)
    return values.bfill(axis=1).iloc[:, 0].fillna("").astype("string")


def prepare_documents(
    frame: "pd.DataFrame",
    *,
    source_id: str | None = None,
    source_file: str | None = None,
    source_family: str | None = None,
) -> "pd.DataFrame":
    """Clean and harmonise one of the four document tables.

    The original source columns remain available.  Canonical columns are
    added so the four sources can be concatenated safely:

    ``document_title``, ``document_text``, ``author``, ``organization``,
    ``access_status``, ``text_clean``, ``search_text``, ``word_count``,
    ``character_count``, ``document_year`` and ``document_month``.
    """

    _require_pandas()
    result = frame.copy()
    result = _clean_string_columns(result)

    if "document_id" in result.columns:
        result["document_id"] = result["document_id"].astype("string").str.strip()

    if "document_date" in result.columns:
        result["document_date_raw"] = result["document_date"].astype("string")
        result["document_date"] = pd.to_datetime(
            result["document_date"], errors="coerce"
        )

    result["document_title"] = _coalesce_columns(
        result, ["title", "subject_line", "document_type"]
    )
    result["document_text"] = _coalesce_columns(result, ["text"])
    result["author"] = _coalesce_columns(
        result, ["author_name", "author_license_number"]
    )
    result["organization"] = _coalesce_columns(result, ["author_organization"])
    result["access_status"] = _coalesce_columns(
        result,
        [
            "public_or_restricted",
            "visibility_level",
            "confidentiality_class",
            "publication_status",
        ],
    )

    result["text_clean"] = result["document_text"].map(normalize_text)
    result["search_text"] = (
        result["document_title"].map(normalize_text).str.cat(
            result["text_clean"], sep=" ", na_rep=""
        )
    ).map(normalize_text)
    result["word_count"] = result["text_clean"].map(
        lambda value: len(tokenize_text(value, remove_numbers=False))
    )
    result["character_count"] = result["text_clean"].str.len().fillna(0).astype(int)

    if "document_date" in result.columns:
        result["document_year"] = result["document_date"].dt.year.astype("Int64")
        result["document_month"] = result["document_date"].dt.to_period("M").astype(
            "string"
        )
    else:
        result["document_year"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
        result["document_month"] = pd.Series(
            "", index=result.index, dtype="string"
        )

    result["source_id"] = source_id or result.get(
        "source_id", pd.Series("", index=result.index, dtype="string")
    )
    result["source_file"] = source_file or result.get(
        "source_file", pd.Series("", index=result.index, dtype="string")
    )
    result["source_family"] = source_family or result.get(
        "source_family", pd.Series("", index=result.index, dtype="string")
    )

    return result


def load_document_file(
    path: str | Path,
    *,
    source_id: str | None = None,
    source_family: str | None = None,
    encoding: str = "utf-8",
) -> "pd.DataFrame":
    """Load and prepare one document CSV, including multiline text fields."""

    _require_pandas()
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    frame = pd.read_csv(
        csv_path,
        dtype="string",
        keep_default_na=False,
        encoding=encoding,
        low_memory=False,
    )
    resolved_source_id = source_id or csv_path.stem
    return prepare_documents(
        frame,
        source_id=resolved_source_id,
        source_file=str(csv_path),
        source_family=source_family or "",
    )


def _resolve_analysis_folder(folder: str | None = None) -> str:
    selected = folder if folder is not None else ACTIVE_ANALYSIS_FOLDER
    normalized = selected.strip().lower()
    normalized = FOLDER_ALIASES.get(normalized, normalized)
    if normalized not in ANALYSIS_FOLDERS:
        choices = ", ".join(ANALYSIS_FOLDERS)
        raise ValueError(
            f"Dossier d’analyse inconnu : {selected!r}. Choisir parmi : {choices}."
        )
    return normalized


def set_analysis_folder(folder: str) -> str:
    """Set and return the global document folder used by the notebook.

    Accepted values are ``all``, ``public_records``, ``health`` and
    ``ecology``.  The aliases ``public``, ``medical`` and ``ecological`` are
    also accepted.
    """

    global ACTIVE_ANALYSIS_FOLDER
    ACTIVE_ANALYSIS_FOLDER = _resolve_analysis_folder(folder)
    return ACTIVE_ANALYSIS_FOLDER


def get_analysis_folder() -> str:
    """Return the currently selected global analysis folder."""

    return _resolve_analysis_folder()


def load_active_documents(
    data_dir: str | Path | None = None,
    *,
    folder: str | None = None,
    encoding: str = "utf-8",
) -> "pd.DataFrame":
    """Load documents for the selected folder.

    If ``folder`` is omitted, the global value set by
    :func:`set_analysis_folder` is used.  Passing ``folder`` is useful when a
    notebook wants to avoid changing global state temporarily.
    """

    selected = _resolve_analysis_folder(folder)
    return load_all_documents(
        data_dir=data_dir,
        sources=ANALYSIS_FOLDERS[selected],
        encoding=encoding,
    )


def output_directory(
    output_root: str | Path | None = None,
    *,
    folder: str | None = None,
    create: bool = False,
) -> Path:
    """Return the output directory corresponding to the selected folder."""

    selected = _resolve_analysis_folder(folder)
    root = Path(output_root) if output_root is not None else PROJECT_ROOT / "outputs"
    directory = root / selected
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def output_path(
    filename: str | Path,
    output_root: str | Path | None = None,
    *,
    folder: str | None = None,
    create: bool = False,
) -> Path:
    """Build a safe output path inside the selected folder's output directory."""

    name = Path(filename).name
    if not name or name in {".", ".."}:
        raise ValueError("Le nom du fichier de sortie ne peut pas être vide")
    if Path(name).suffix == "":
        name = f"{name}.csv"
    return output_directory(output_root, folder=folder, create=create) / name


def save_output(
    frame: "pd.DataFrame",
    filename: str | Path,
    output_root: str | Path | None = None,
    *,
    folder: str | None = None,
    index: bool = False,
    encoding: str = "utf-8",
) -> Path:
    """Save a DataFrame in the output directory for the selected folder."""

    _require_pandas()
    path = output_path(filename, output_root, folder=folder, create=True)
    frame.to_csv(path, index=index, encoding=encoding)
    return path


def load_all_documents(
    data_dir: str | Path | None = None,
    *,
    sources: Iterable[str] | None = None,
    encoding: str = "utf-8",
) -> "pd.DataFrame":
    """Load the four document CSVs into one harmonised DataFrame.

    Parameters
    ----------
    data_dir:
        Project root or another directory containing the ``data`` folder.
        It defaults to the directory containing this module.
    sources:
        Optional subset of keys from :data:`DOCUMENT_FILES`.
    """

    _require_pandas()
    root = Path(data_dir) if data_dir is not None else PROJECT_ROOT
    selected = list(sources) if sources is not None else list(DOCUMENT_FILES)
    unknown = sorted(set(selected) - set(DOCUMENT_FILES))
    if unknown:
        raise ValueError(
            f"Sources inconnues : {', '.join(unknown)}. "
            f"Choisir parmi : {', '.join(DOCUMENT_FILES)}"
        )

    frames = []
    for source_id in selected:
        relative_path = DOCUMENT_FILES[source_id]
        frames.append(
            load_document_file(
                root / relative_path,
                source_id=source_id,
                source_family=DOCUMENT_FAMILIES[source_id],
                encoding=encoding,
            )
        )

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def sort_documents(
    documents: "pd.DataFrame",
    *,
    by: str = "document_date",
    ascending: bool = True,
    na_position: str = "last",
) -> "pd.DataFrame":
    """Return documents sorted stably by one column."""

    _require_pandas()
    if by not in documents.columns:
        raise KeyError(f"Colonne de tri absente : {by}")
    return documents.sort_values(
        by=by,
        ascending=ascending,
        na_position=na_position,
        kind="stable",
    ).reset_index(drop=True)


def filter_documents(
    documents: "pd.DataFrame",
    *,
    query: str | None = None,
    document_types: str | Iterable[str] | None = None,
    source_ids: str | Iterable[str] | None = None,
    access_status: str | Iterable[str] | None = None,
    author: str | None = None,
    after: str | None = None,
    before: str | None = None,
    regex: bool = False,
    case: bool = False,
) -> "pd.DataFrame":
    """Filter documents by text, metadata and/or date.

    ``query`` searches the canonical ``search_text`` column, which contains
    both the title/subject and the document body.  With ``regex=False`` the
    query is treated as literal text.
    """

    _require_pandas()
    result = documents.copy()
    mask = pd.Series(True, index=result.index, dtype="boolean")

    if query:
        search_column = "search_text" if "search_text" in result else "text"
        if search_column not in result.columns:
            raise KeyError("Aucune colonne textuelle disponible pour la recherche")
        pattern = query if regex else re.escape(query)
        text_mask = result[search_column].astype("string").str.contains(
            pattern, case=case, regex=True, na=False
        )
        mask &= text_mask

    if document_types is not None:
        if "document_type" not in result.columns:
            raise KeyError("Colonne absente : document_type")
        mask &= result["document_type"].isin(_as_list(document_types))

    if source_ids is not None:
        if "source_id" not in result.columns:
            raise KeyError("Colonne absente : source_id")
        mask &= result["source_id"].isin(_as_list(source_ids))

    if access_status is not None:
        if "access_status" not in result.columns:
            raise KeyError("Colonne absente : access_status")
        mask &= result["access_status"].isin(_as_list(access_status))

    if author is not None:
        if "author" not in result.columns:
            raise KeyError("Colonne absente : author")
        author_pattern = re.escape(author)
        mask &= result["author"].astype("string").str.contains(
            author_pattern, case=case, regex=True, na=False
        )

    if after is not None or before is not None:
        if "document_date" not in result.columns:
            raise KeyError("Colonne absente : document_date")
        dates = pd.to_datetime(result["document_date"], errors="coerce")
        if after is not None:
            mask &= dates >= pd.Timestamp(after)
        if before is not None:
            mask &= dates <= pd.Timestamp(before)

    return result.loc[mask.fillna(False)].reset_index(drop=True)


def category_counts(
    documents: "pd.DataFrame",
    column: str,
    *,
    include_missing: bool = True,
) -> "pd.DataFrame":
    """Count and rank the values of a categorical column."""

    _require_pandas()
    if column not in documents.columns:
        raise KeyError(f"Colonne absente : {column}")

    values = documents[column].astype("string")
    if include_missing:
        values = values.fillna("").replace("", "<missing>")
        counts = values.value_counts(dropna=False)
    else:
        counts = values.value_counts(dropna=True)

    return counts.rename_axis(column).reset_index(name="document_count")


def document_summary(
    documents: "pd.DataFrame",
    *,
    group_by: str = "source_id",
) -> "pd.DataFrame":
    """Summarise document count, length and date range by source or type."""

    _require_pandas()
    if group_by not in documents.columns:
        raise KeyError(f"Colonne absente : {group_by}")

    frame = documents.copy()
    if "word_count" not in frame.columns or "text_clean" not in frame.columns:
        frame = prepare_documents(frame)

    summary = (
        frame.groupby(group_by, dropna=False)
        .agg(
            document_count=("document_id", "nunique"),
            total_words=("word_count", "sum"),
            mean_words=("word_count", "mean"),
            median_words=("word_count", "median"),
            empty_text=("text_clean", lambda values: (values == "").sum()),
        )
        .reset_index()
    )

    if "document_date" in frame.columns:
        dates = frame.assign(
            _valid_date=pd.to_datetime(frame["document_date"], errors="coerce")
        )
        date_summary = (
            dates.groupby(group_by, dropna=False)["_valid_date"]
            .agg(first_date="min", last_date="max")
            .reset_index()
        )
        summary = summary.merge(date_summary, on=group_by, how="left")

    return summary.sort_values("document_count", ascending=False).reset_index(drop=True)


def quality_report(documents: "pd.DataFrame") -> "pd.DataFrame":
    """Return basic data-quality checks for the harmonised corpus."""

    _require_pandas()
    rows = len(documents)
    metrics: dict[str, int | float] = {"rows": rows}

    if "document_id" in documents.columns:
        metrics["duplicate_document_ids"] = int(
            documents["document_id"].duplicated(keep=False).sum()
        )
        metrics["missing_document_ids"] = int(
            documents["document_id"].astype("string").str.strip().eq("").sum()
        )
    if "text_clean" in documents.columns:
        metrics["empty_text"] = int(documents["text_clean"].eq("").sum())
    elif "text" in documents.columns:
        metrics["empty_text"] = int(
            documents["text"].map(normalize_text).eq("").sum()
        )
    if "document_title" in documents.columns:
        metrics["empty_titles"] = int(documents["document_title"].eq("").sum())
    if "document_date" in documents.columns:
        dates = pd.to_datetime(documents["document_date"], errors="coerce")
        metrics["missing_or_invalid_dates"] = int(dates.isna().sum())

    report = pd.DataFrame(
        {"check": list(metrics), "value": list(metrics.values())}
    )
    if rows:
        report["percentage"] = report["value"].map(
            lambda value: round(100 * value / rows, 2)
            if isinstance(value, (int, float))
            else pd.NA
        )
    return report


def spearman_correlation(
    documents: "pd.DataFrame",
    *,
    columns: Sequence[str] | None = None,
    min_periods: int = 2,
) -> "pd.DataFrame":
    """Return a Spearman correlation matrix for numeric document features.

    By default, every numeric column is used.  On a prepared document frame
    this includes, for example, ``word_count``, ``character_count`` and
    ``document_year``.  Columns can be restricted explicitly when the
    notebook needs a particular comparison.
    """

    _require_pandas()
    frame = documents
    if "word_count" not in frame.columns or "text_clean" not in frame.columns:
        frame = prepare_documents(frame)

    if columns is None:
        numeric = frame.select_dtypes(include="number").copy()
    else:
        missing = sorted(set(columns) - set(frame.columns))
        if missing:
            raise KeyError(f"Colonnes absentes pour la corrélation : {', '.join(missing)}")
        numeric = frame[list(columns)].apply(pd.to_numeric, errors="coerce")

    numeric = numeric.dropna(axis=1, how="all")
    if numeric.shape[1] < 2:
        raise ValueError(
            "La corrélation de Spearman nécessite au moins deux colonnes numériques."
        )
    return numeric.corr(method="spearman", min_periods=min_periods)


def spearman_correlation_by_group(
    documents: "pd.DataFrame",
    *,
    group_by: str = "source_id",
    columns: Sequence[str] | None = None,
    min_periods: int = 2,
) -> dict[object, "pd.DataFrame"]:
    """Return one Spearman matrix for every source or document type."""

    _require_pandas()
    if group_by not in documents.columns:
        raise KeyError(f"Colonne de regroupement absente : {group_by}")

    matrices: dict[object, "pd.DataFrame"] = {}
    for group_value, group in documents.groupby(group_by, dropna=False):
        try:
            matrices[group_value] = spearman_correlation(
                group, columns=columns, min_periods=min_periods
            )
        except ValueError:
            # A group with constant or absent numeric data does not produce a
            # meaningful matrix, so it is omitted rather than fabricated.
            continue
    return matrices


def word_frequencies(
    documents: "pd.DataFrame",
    *,
    text_column: str = "text_clean",
    stopwords: Iterable[str] | None = DEFAULT_ENGLISH_STOPWORDS,
    min_length: int = 2,
    min_frequency: int = 1,
) -> "pd.DataFrame":
    """Return term frequency and document frequency for the corpus.

    Pass ``stopwords=()`` to keep every token, or provide a custom set for a
    different language/domain vocabulary.
    """

    _require_pandas()
    if text_column not in documents.columns:
        raise KeyError(f"Colonne textuelle absente : {text_column}")

    ignored = {word.lower() for word in stopwords} if stopwords is not None else set()
    term_counts: Counter[str] = Counter()
    document_counts: Counter[str] = Counter()

    for value in documents[text_column].fillna(""):
        tokens = [
            token
            for token in tokenize_text(value, min_length=min_length)
            if token not in ignored
        ]
        term_counts.update(tokens)
        document_counts.update(set(tokens))

    result = pd.DataFrame(
        [
            {
                "term": term,
                "term_frequency": count,
                "document_frequency": document_counts[term],
            }
            for term, count in term_counts.items()
            if count >= min_frequency
        ]
    )
    if result.empty:
        return pd.DataFrame(
            columns=["term", "term_frequency", "document_frequency"]
        )
    return result.sort_values(
        ["term_frequency", "document_frequency", "term"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def ngram_frequencies(
    documents: "pd.DataFrame",
    *,
    n: int = 2,
    text_column: str = "text_clean",
    stopwords: Iterable[str] | None = DEFAULT_ENGLISH_STOPWORDS,
    min_frequency: int = 1,
) -> "pd.DataFrame":
    """Return ranked word n-grams, such as bigrams or trigrams."""

    _require_pandas()
    if n < 1:
        raise ValueError("n doit être supérieur ou égal à 1")
    if text_column not in documents.columns:
        raise KeyError(f"Colonne textuelle absente : {text_column}")

    ignored = {word.lower() for word in stopwords} if stopwords is not None else set()
    ngram_counts: Counter[tuple[str, ...]] = Counter()
    document_counts: Counter[tuple[str, ...]] = Counter()

    for value in documents[text_column].fillna(""):
        tokens = [
            token
            for token in tokenize_text(value)
            if token not in ignored
        ]
        ngrams = list(zip(*(tokens[index:] for index in range(n))))
        ngram_counts.update(ngrams)
        document_counts.update(set(ngrams))

    rows = [
        {
            "ngram": " ".join(ngram),
            "term_frequency": count,
            "document_frequency": document_counts[ngram],
        }
        for ngram, count in ngram_counts.items()
        if count >= min_frequency
    ]
    return pd.DataFrame(
        rows,
        columns=["ngram", "term_frequency", "document_frequency"],
    ).sort_values(
        ["term_frequency", "document_frequency", "ngram"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def word_frequencies_by_group(
    documents: "pd.DataFrame",
    *,
    group_by: str = "source_id",
    text_column: str = "text_clean",
    stopwords: Iterable[str] | None = DEFAULT_ENGLISH_STOPWORDS,
    min_length: int = 2,
    min_frequency: int = 1,
) -> "pd.DataFrame":
    """Compute word frequencies separately for each source or document type."""

    _require_pandas()
    if group_by not in documents.columns:
        raise KeyError(f"Colonne de regroupement absente : {group_by}")

    parts = []
    for group_value, group in documents.groupby(group_by, dropna=False):
        frequencies = word_frequencies(
            group,
            text_column=text_column,
            stopwords=stopwords,
            min_length=min_length,
            min_frequency=min_frequency,
        )
        if not frequencies.empty:
            frequencies.insert(0, group_by, group_value)
            parts.append(frequencies)

    if not parts:
        return pd.DataFrame(
            columns=[group_by, "term", "term_frequency", "document_frequency"]
        )
    return pd.concat(parts, ignore_index=True)


def search_documents(
    documents: "pd.DataFrame",
    query: str,
    *,
    regex: bool = False,
    case: bool = False,
) -> "pd.DataFrame":
    """Convenience wrapper around :func:`filter_documents` for text search."""

    return filter_documents(documents, query=query, regex=regex, case=case)


__all__ = [
    "ACTIVE_ANALYSIS_FOLDER",
    "ANALYSIS_FOLDERS",
    "DEFAULT_ENGLISH_STOPWORDS",
    "DOCUMENT_FAMILIES",
    "DOCUMENT_FILES",
    "FOLDER_ALIASES",
    "PROJECT_ROOT",
    "category_counts",
    "document_summary",
    "filter_documents",
    "get_analysis_folder",
    "load_active_documents",
    "load_all_documents",
    "load_document_file",
    "ngram_frequencies",
    "normalize_text",
    "output_directory",
    "output_path",
    "prepare_documents",
    "quality_report",
    "save_output",
    "search_documents",
    "set_analysis_folder",
    "sort_documents",
    "spearman_correlation",
    "spearman_correlation_by_group",
    "tokenize_text",
    "word_frequencies",
    "word_frequencies_by_group",
]
