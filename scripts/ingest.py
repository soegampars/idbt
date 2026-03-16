"""Ingestion helper functions for the IDBT pipeline."""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = REPO_ROOT / "inbox"
ARCHIVE_DIR = REPO_ROOT / "archive"
REF_DIR = REPO_ROOT / "data" / "ref"
FACTS_DIR = REPO_ROOT / "data" / "facts"

# String columns that must never be cast to int
_STRING_COLS = {"kode_wilayah", "kode_provinsi", "kode_induk", "kode_baru", "kbli"}


# ---------------------------------------------------------------------------
# Inbox helpers
# ---------------------------------------------------------------------------

def list_inbox():
    """Return sorted list of CSV file paths in inbox/. Skip README.md and .gitkeep."""
    if not INBOX_DIR.exists():
        print(f"Warning: {INBOX_DIR} does not exist.")
        return []
    return sorted(
        p for p in INBOX_DIR.iterdir()
        if p.suffix.lower() == ".csv" and p.name not in {"README.md", ".gitkeep"}
    )


def preview_csv(path, n=5):
    """Read a CSV and print: filename, shape, dtypes, and first n rows."""
    path = Path(path)
    if not path.exists():
        print(f"Error: {path} not found.")
        return
    # Read all key columns as strings
    dtype = {c: str for c in _STRING_COLS}
    df = pd.read_csv(path, dtype=dtype)
    print(f"File: {path.name}")
    print(f"Shape: {df.shape}")
    print(f"Dtypes:\n{df.dtypes}")
    print(df.head(n))
    return df


def parse_filename(path):
    """
    Parse inbox filename like 'industri_kbli_2013.csv' into:
    {"domain": "industri", "dimension": "kbli", "year": 2013}
    Return None with a warning if filename doesn't match pattern.
    """
    name = Path(path).stem  # e.g. "industri_kbli_2013"
    match = re.match(r"^(.+?)_([a-z]+)_(\d{4})$", name)
    if not match:
        print(f"Warning: filename '{Path(path).name}' does not match pattern "
              "{{domain}}_{{dimension}}_{{year}}.csv")
        return None
    return {
        "domain": match.group(1),
        "dimension": match.group(2),
        "year": int(match.group(3)),
    }


# ---------------------------------------------------------------------------
# Reference table helpers
# ---------------------------------------------------------------------------

def load_ref(name):
    """
    Load a reference Parquet table. name is like 'ref_wilayah'.
    Returns a DataFrame. Path is data/ref/{name}.parquet.
    """
    path = REF_DIR / f"{name}.parquet"
    if not path.exists():
        print(f"Error: reference table {path} not found.")
        return pd.DataFrame()
    return pd.read_parquet(path)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_wilayah(df, kode_col="kode_wilayah"):
    """
    Check that all values in df[kode_col] exist in ref_wilayah.
    Return a list of invalid codes. Return empty list if all valid.
    """
    if kode_col not in df.columns:
        print(f"Warning: column '{kode_col}' not in DataFrame.")
        return []
    ref = load_ref("ref_wilayah")
    if ref.empty:
        print("Warning: ref_wilayah is empty, skipping validation.")
        return []
    valid_codes = set(ref["kode_wilayah"].astype(str))
    incoming = set(df[kode_col].astype(str))
    invalid = sorted(incoming - valid_codes)
    if invalid:
        print(f"Found {len(invalid)} invalid wilayah codes: {invalid}")
    return invalid


def validate_no_duplicates(new_long_df, target_path):
    """
    If target_path exists, load it and check whether any rows in new_long_df
    have the same (kode_wilayah or kbli, tahun, indikator_id, publikasi_id).
    Return a DataFrame of duplicates (empty if none).
    """
    target_path = Path(target_path)
    if not target_path.exists():
        return pd.DataFrame()

    existing = pd.read_parquet(target_path)

    # Determine which key column is present
    key_col = "kbli" if "kbli" in new_long_df.columns else "kode_wilayah"
    merge_cols = [key_col, "tahun", "indikator_id", "publikasi_id"]

    # Ensure matching string types for the merge
    for col in [key_col, "indikator_id", "publikasi_id"]:
        if col in existing.columns:
            existing[col] = existing[col].astype(str)
        if col in new_long_df.columns:
            new_long_df[col] = new_long_df[col].astype(str)

    dupes = new_long_df.merge(existing, on=merge_cols, how="inner", suffixes=("_new", "_old"))
    if not dupes.empty:
        print(f"Warning: {len(dupes)} duplicate rows found against {target_path.name}")
    return dupes


# ---------------------------------------------------------------------------
# Transformation
# ---------------------------------------------------------------------------

def to_long_format(df, key_col, tahun, value_columns, indikator_mapping, publikasi_id):
    """
    Transform a wide DataFrame into the standard long fact format.

    Parameters:
    - df: the wide DataFrame
    - key_col: "kbli" or "kode_wilayah"
    - tahun: integer year
    - value_columns: list of column names in df that contain numeric values
    - indikator_mapping: dict mapping column_name -> indikator_id
    - publikasi_id: string

    Returns a DataFrame with columns:
    [key_col, "tahun", "indikator_id", "nilai", "publikasi_id"]
    """
    # Keep only key + value columns
    subset = df[[key_col] + list(value_columns)].copy()

    # Melt wide -> long
    long = pd.melt(
        subset,
        id_vars=[key_col],
        value_vars=value_columns,
        var_name="column_name",
        value_name="nilai",
    )

    # Map column names to indikator_ids
    long["indikator_id"] = long["column_name"].map(indikator_mapping)
    long.drop(columns=["column_name"], inplace=True)

    # Add fixed columns
    long["tahun"] = tahun
    long["publikasi_id"] = publikasi_id

    # Coerce nilai to float and drop NaN
    long["nilai"] = pd.to_numeric(long["nilai"], errors="coerce")
    long = long.dropna(subset=["nilai"]).reset_index(drop=True)

    # Ensure key column is string
    long[key_col] = long[key_col].astype(str)

    # Reorder columns
    long = long[[key_col, "tahun", "indikator_id", "nilai", "publikasi_id"]]
    return long


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def append_to_parquet(long_df, target_path):
    """
    If target_path exists, read it, concatenate with long_df, write back.
    If not, write long_df directly.
    Ensure string columns stay as strings.
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Force known string columns
    for col in long_df.columns:
        if col in _STRING_COLS:
            long_df[col] = long_df[col].astype(str)

    if target_path.exists():
        existing = pd.read_parquet(target_path)
        combined = pd.concat([existing, long_df], ignore_index=True)
        # Re-enforce string types after concat
        for col in combined.columns:
            if col in _STRING_COLS:
                combined[col] = combined[col].astype(str)
        combined.to_parquet(target_path, engine="pyarrow", index=False)
        print(f"Appended {len(long_df)} rows to {target_path}")
    else:
        long_df.to_parquet(target_path, engine="pyarrow", index=False)
        print(f"Created {target_path} with {len(long_df)} rows")


def archive_csv(csv_path):
    """
    Move csv_path to archive/ with a timestamp prefix.
    E.g., inbox/industri_kbli_2013.csv -> archive/20250315_143022_industri_kbli_2013.csv
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = ARCHIVE_DIR / f"{timestamp}_{csv_path.name}"
    shutil.move(str(csv_path), str(dest))
    print(f"Archived to {dest}")


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

def register_indikator(indikator_id, nama_id, nama_en, satuan, seri, catatan=""):
    """
    Append a new row to data/ref/ref_indikator.parquet.
    Check for duplicate indikator_id first — skip and warn if exists.
    """
    path = REF_DIR / "ref_indikator.parquet"
    if not path.exists():
        print(f"Error: {path} not found. Run init_refs.py first.")
        return

    df = pd.read_parquet(path)
    if indikator_id in df["indikator_id"].values:
        print(f"Warning: indikator_id '{indikator_id}' already exists, skipping.")
        return

    new_row = pd.DataFrame([{
        "indikator_id": indikator_id,
        "nama_id": nama_id,
        "nama_en": nama_en,
        "satuan": satuan,
        "seri": seri,
        "catatan": catatan,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_parquet(path, engine="pyarrow", index=False)
    print(f"Registered indikator: {indikator_id}")


def register_publikasi(publikasi_id, judul, seri, tahun, provinsi, url_sumber=""):
    """
    Append a new row to data/ref/ref_publikasi.parquet.
    Check for duplicate publikasi_id first — skip and warn if exists.
    """
    path = REF_DIR / "ref_publikasi.parquet"
    if not path.exists():
        print(f"Error: {path} not found. Run init_refs.py first.")
        return

    df = pd.read_parquet(path)
    if publikasi_id in df["publikasi_id"].values:
        print(f"Warning: publikasi_id '{publikasi_id}' already exists, skipping.")
        return

    new_row = pd.DataFrame([{
        "publikasi_id": publikasi_id,
        "judul": judul,
        "seri": seri,
        "tahun": tahun,
        "provinsi": provinsi,
        "url_sumber": url_sumber,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_parquet(path, engine="pyarrow", index=False)
    print(f"Registered publikasi: {publikasi_id}")
