#!/usr/bin/env python3
"""
prepare_ingest.py
Prepare raw article data for the sovereign ingestion pipeline.

- Reads raw files (CSV, JSON, Excel) from a source directory.
- Renames/maps columns to match the master ontology schema:
    concept_id (str, primary key)
    article_title (str)
    pillar_category (str)
    timestamp (ISO-8601 string)
    summary (str, optional)
- Validates required fields and uniqueness of concept_id.
- Optionally generates UUID4 for missing concept_id.
- Writes cleaned data as Parquet to a staging directory.
- Optionally moves problematic source files to quarantine.
- Logs validation results to integrity_events.log (via caller).
"""

import argparse
import logging
import os
import sys
import uuid
from pathlib import Path

import pandas as pd

# -------------------------- Configuration --------------------------
CANONICAL_FIELDS = ["concept_id", "article_title", "pillar_category", "timestamp", "summary"]
REQUIRED_FIELDS = ["concept_id", "article_title", "pillar_category", "timestamp"]

COLUMN_MAP = {
    # concept_id
    "id": "concept_id",
    "ConceptID": "concept_id",
    "Concept ID": "concept_id",
    "article_id": "concept_id",
    "uid": "concept_id",
    # article_title
    "title": "article_title",
    "Article Title": "article_title",
    "headline": "article_title",
    # pillar_category
    "pillar": "pillar_category",
    "Pillar": "pillar_category",
    "category": "pillar_category",
    "Category": "pillar_category",
    "topic": "pillar_category",
    # timestamp
    "date": "timestamp",
    "Date": "timestamp",
    "published_at": "timestamp",
    "Published At": "timestamp",
    "pub_date": "timestamp",
    # summary
    "abstract": "summary",
    "Abstract": "summary",
    "description": "summary",
    "Description": "summary",
    "summary": "summary",
}

STAGING_DIR = Path(os.getenv("INGEST_STAGING_DIR", "/root/acaciafund/tmp_ingest"))
QUARANTINE_DIR = Path(os.getenv("INGEST_QUARANTINE_DIR", "/root/acaciafund/quarantine"))
LOG_FILE = Path(os.getenv("INGEST_LOG_FILE", "/root/acaciafund/integrity_events.log"))

# -------------------------- Logging Setup --------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# -------------------------- Helper Functions --------------------------
def _detect_file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".xls", ".xlsx"}:
        return "excel"
    if suffix == ".json":
        return "json"
    raise ValueError(f"Unsupported file type: {suffix}")


def _read_file(path: str) -> pd.DataFrame:
    p = Path(path)
    ftype = _detect_file_type(p)
    if ftype == "csv":
        return pd.read_csv(p, dtype=str)
    if ftype == "excel":
        return pd.read_excel(p, dtype=str)
    if ftype == "json":
        return pd.read_json(p, dtype=str)
    raise RuntimeError(f"Unsupported file type: {ftype}")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = {}
    for col in df.columns:
        stripped = col.strip()
        mapped = COLUMN_MAP.get(stripped, stripped)
        new_cols[col] = mapped
    return df.rename(columns=new_cols)


def _validate_and_cast(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure required columns exist
    missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # concept_id: string, strip, fill missing with UUID, ensure unique
    df["concept_id"] = df["concept_id"].astype(str).str.strip()
    # Fill empty or NaN
    mask_empty = df["concept_id"].isna() | (df["concept_id"] == "")
    if mask_empty.any():
        df.loc[mask_empty, "concept_id"] = [str(uuid.uuid4()) for _ in range(mask_empty.sum())]
    # Check duplicates
    duplicated = df["concept_id"].duplicated()
    if duplicated.any():
        dup_vals = df.loc[duplicated, "concept_id"].drop_duplicates().tolist()
        raise ValueError(f"Duplicate concept_id values found: {dup_vals}")

    # article_title and pillar_category: string, strip, fill NaN
    for col in ["article_title", "pillar_category"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # timestamp: parse to datetime then ISO-8601 string
    def parse_ts(val):
        if pd.isna(val) or val == "":
            return pd.NaT
        try:
            ts = pd.to_datetime(val, utc=False)
            return ts.isoformat()
        except Exception:
            return pd.NaT

    df["timestamp"] = df["timestamp"].apply(parse_ts)
    invalid_ts = df["timestamp"].isna()
    if bool(invalid_ts.any()):
        bad_rows = df.index[invalid_ts].tolist()
        raise ValueError(f"Invalid timestamp values in rows: {bad_rows}")

    # summary optional
    if "summary" in df.columns:
        df["summary"] = df["summary"].fillna("").astype(str).str.strip()
    else:
        df["summary"] = ""

    # Reorder columns: canonical first, then any extra
    extra_cols = [c for c in df.columns if c not in CANONICAL_FIELDS]
    df = df.loc[:, CANONICAL_FIELDS + extra_cols].copy()
    return df


def process_file(src_path: Path, quarantine: bool = False) -> tuple[int, int]:
    logger.info(f"Processing {src_path}")
    try:
        df_raw = _read_file(str(src_path))
        logger.info(f"Read {len(df_raw)} rows, columns: {list(df_raw.columns)}")
        df_norm = _normalize_columns(df_raw)
        logger.debug(f"After column normalization: {list(df_norm.columns)}")
        df_valid = _validate_and_cast(df_norm)
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        out_file = STAGING_DIR / f"{src_path.stem}_cleaned.parquet"
        df_valid.to_parquet(out_file, index=False)
        logger.info(f"Written {len(df_valid)} valid rows to {out_file}")
        return len(df_valid), 0
    except Exception as e:
        logger.error(f"Failed to process {src_path}: {e}")
        if quarantine:
            QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
            dest = QUARANTINE_DIR / f"{src_path.name}.failed_{int(pd.Timestamp.now().timestamp())}"
            src_path.rename(dest)
            logger.info(f"Moved problematic file to quarantine: {dest}")
        return 0, 1


def main():
    parser = argparse.ArgumentParser(description="Prepare raw article data for ingestion pipeline.")
    parser.add_argument(
        "--src-dir",
        type=str,
        required=True,
        help="Directory containing raw input files (CSV, JSON, Excel).",
    )
    parser.add_argument(
        "--quarantine",
        action="store_true",
        help="Move source files that fail validation to the quarantine directory.",
    )
    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    if not src_dir.is_dir():
        logger.error(f"Source directory does not exist: {src_dir}")
        sys.exit(1)

    total_valid = 0
    total_invalid = 0
    for src_file in src_dir.iterdir():
        if src_file.is_file():
            v, i = process_file(src_file, quarantine=args.quarantine)
            total_valid += v
            total_invalid += i

    logger.info(f"Finished. Valid rows: {total_valid}, Invalid files: {total_invalid}")
    sys.exit(0 if total_valid > 0 else 1)


if __name__ == "__main__":
    main()
