"""Validate Parquet files for data integrity.

Usage:
    python scripts/validate.py                              # validate everything
    python scripts/validate.py data/facts/industri.parquet  # validate one file
"""

import io
import sys
from pathlib import Path

import pandas as pd

# Ensure stdout can handle unicode on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
REF_DIR = REPO_ROOT / "data" / "ref"
FACTS_DIR = REPO_ROOT / "data" / "facts"

# Counters
_passed = 0
_failed = 0
_warnings = 0


def _pass(msg):
    global _passed
    _passed += 1
    print(f"  \u2713 {msg}")


def _fail(msg):
    global _failed
    _failed += 1
    print(f"  \u2717 {msg}")


def _warn(msg):
    global _warnings
    _warnings += 1
    print(f"  \u26a0 {msg}")


# ---------------------------------------------------------------------------
# Generic checks
# ---------------------------------------------------------------------------

def read_parquet_safe(path):
    """Try to read a Parquet file. Return DataFrame or None on failure."""
    try:
        df = pd.read_parquet(path)
        return df
    except Exception as e:
        _fail(f"Could not read file: {e}")
        return None


def check_required_columns(df, required):
    """Check that all required columns are present."""
    missing = set(required) - set(df.columns)
    if missing:
        _fail(f"Missing required columns: {sorted(missing)}")
        return False
    _pass("Required columns present")
    return True


def check_string_dtype(df, col):
    """Check that a column has string/object dtype."""
    if df[col].dtype in ("object", "string", "str"):
        _pass(f"{col} is string type")
        return True
    _fail(f"{col} has dtype {df[col].dtype}, expected string/object")
    return False


def check_no_duplicates(df, col):
    """Check for duplicate values in a column."""
    dupes = df[col].duplicated().sum()
    if dupes == 0:
        _pass(f"No duplicate {col}")
        return True
    _fail(f"{dupes} duplicate {col} values found")
    return False


# ---------------------------------------------------------------------------
# Table-specific validators
# ---------------------------------------------------------------------------

def validate_ref_wilayah(df):
    if not check_required_columns(df, ["kode_wilayah", "nama_wilayah", "tingkat", "kode_provinsi"]):
        return
    check_string_dtype(df, "kode_wilayah")
    # tingkat values
    valid_tingkat = {"nasional", "provinsi", "kabupaten", "kota"}
    actual = set(df["tingkat"].dropna().unique())
    invalid = actual - valid_tingkat
    if invalid:
        _fail(f"Invalid tingkat values: {sorted(invalid)}")
    else:
        _pass("Valid tingkat values")
    check_no_duplicates(df, "kode_wilayah")


def validate_ref_pemekaran(df):
    if not check_required_columns(df, ["kode_induk", "kode_baru", "tahun_efektif"]):
        return
    check_string_dtype(df, "kode_induk")
    check_string_dtype(df, "kode_baru")


def validate_ref_publikasi(df):
    if not check_required_columns(df, ["publikasi_id", "judul", "seri", "tahun", "provinsi"]):
        return
    check_no_duplicates(df, "publikasi_id")


def validate_ref_indikator(df):
    if not check_required_columns(df, ["indikator_id", "nama_id", "nama_en", "satuan", "seri"]):
        return
    if len(df) == 0:
        _warn("No data rows yet (this is OK)")
    else:
        check_no_duplicates(df, "indikator_id")


def validate_fact(df, path):
    """Validate a fact table in data/facts/."""
    if not check_required_columns(df, ["tahun", "indikator_id", "nilai", "publikasi_id"]):
        return

    # Must have at least one key column
    has_wilayah = "kode_wilayah" in df.columns
    has_kbli = "kbli" in df.columns
    if not has_wilayah and not has_kbli:
        _fail("Must have at least one of: kode_wilayah, kbli")
        return
    _pass("Key column present (kode_wilayah and/or kbli)")

    # tahun range
    out_of_range = df[(df["tahun"] < 1970) | (df["tahun"] > 2030)]
    if len(out_of_range) > 0:
        _fail(f"{len(out_of_range)} rows with tahun outside 1970–2030")
    else:
        _pass("All tahun values in range 1970–2030")

    # nilai is numeric
    if pd.api.types.is_numeric_dtype(df["nilai"]):
        _pass("nilai is numeric")
    else:
        _fail("nilai is not numeric")

    # Cross-reference: kode_wilayah (only check non-null values)
    if has_wilayah:
        ref_wil = _load_ref("ref_wilayah")
        if ref_wil is not None:
            valid_codes = set(ref_wil["kode_wilayah"].astype(str))
            actual_codes = set(df["kode_wilayah"].dropna().astype(str))
            invalid = actual_codes - valid_codes
            if invalid:
                _fail(f"{len(invalid)} kode_wilayah not in ref_wilayah: {sorted(invalid)[:10]}")
            else:
                _pass("All kode_wilayah exist in ref_wilayah")

    # Cross-reference: indikator_id
    ref_ind = _load_ref("ref_indikator")
    if ref_ind is not None and len(ref_ind) > 0:
        valid_ids = set(ref_ind["indikator_id"].astype(str))
        actual_ids = set(df["indikator_id"].astype(str))
        invalid = actual_ids - valid_ids
        if invalid:
            _fail(f"{len(invalid)} indikator_id not in ref_indikator: {sorted(invalid)[:10]}")
        else:
            _pass("All indikator_id exist in ref_indikator")

    # Cross-reference: publikasi_id
    ref_pub = _load_ref("ref_publikasi")
    if ref_pub is not None:
        valid_ids = set(ref_pub["publikasi_id"].astype(str))
        actual_ids = set(df["publikasi_id"].astype(str))
        invalid = actual_ids - valid_ids
        if invalid:
            _fail(f"{len(invalid)} publikasi_id not in ref_publikasi: {sorted(invalid)[:10]}")
        else:
            _pass("All publikasi_id exist in ref_publikasi")

    # No duplicate rows — check each key subset independently
    # A fact table may have rows keyed by kbli and rows keyed by kode_wilayah
    total_dupes = 0
    if has_kbli:
        kbli_rows = df[df["kbli"].notna()]
        if len(kbli_rows) > 0:
            dup_cols = ["kbli", "tahun", "indikator_id", "publikasi_id"]
            total_dupes += kbli_rows.duplicated(subset=dup_cols).sum()
    if has_wilayah:
        wil_rows = df[df["kode_wilayah"].notna()]
        if len(wil_rows) > 0:
            dup_cols = ["kode_wilayah", "tahun", "indikator_id", "publikasi_id"]
            total_dupes += wil_rows.duplicated(subset=dup_cols).sum()
    if total_dupes > 0:
        _fail(f"{total_dupes} duplicate rows found")
    else:
        _pass("No duplicate rows")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ref_cache = {}


def _load_ref(name):
    """Load a reference table with caching. Returns DataFrame or None."""
    if name in _ref_cache:
        return _ref_cache[name]
    path = REF_DIR / f"{name}.parquet"
    if not path.exists():
        _warn(f"Reference table {path} not found, skipping cross-reference check")
        return None
    df = pd.read_parquet(path)
    _ref_cache[name] = df
    return df


# Dispatch table for ref validators
_REF_VALIDATORS = {
    "ref_wilayah": validate_ref_wilayah,
    "ref_pemekaran": validate_ref_pemekaran,
    "ref_publikasi": validate_ref_publikasi,
    "ref_indikator": validate_ref_indikator,
}


def validate_file(path):
    """Validate a single Parquet file."""
    path = Path(path)
    df = read_parquet_safe(path)
    if df is None:
        return

    # Print header with relative path from repo root
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        rel = path
    print(f"\U0001f4c4 {rel} ({len(df)} rows, {len(df.columns)} columns)")

    # Determine which validator to use
    stem = path.stem
    if stem in _REF_VALIDATORS:
        _REF_VALIDATORS[stem](df)
    elif FACTS_DIR in path.parents or path.parent.name == "facts":
        validate_fact(df, path)
    else:
        _warn(f"No specific validator for {stem}, basic read OK")


def validate_all():
    """Validate all Parquet files in data/ref/ and data/facts/."""
    # Reference tables (in consistent order)
    for name in ["ref_wilayah", "ref_pemekaran", "ref_publikasi", "ref_indikator"]:
        path = REF_DIR / f"{name}.parquet"
        if path.exists():
            validate_file(path)
        else:
            print(f"\U0001f4c4 {path.relative_to(REPO_ROOT)}")
            _warn(f"File not found")

    # Fact tables
    if FACTS_DIR.exists():
        for path in sorted(FACTS_DIR.glob("*.parquet")):
            validate_file(path)


def main():
    if len(sys.argv) > 1:
        # Validate specific file(s)
        for arg in sys.argv[1:]:
            path = Path(arg)
            if not path.is_absolute():
                path = REPO_ROOT / path
            validate_file(path)
    else:
        validate_all()

    print()
    print(f"Validation complete: {_passed} passed, {_failed} failed, {_warnings} warnings")
    if _failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
