# IDBT — Project Instructions for Claude Code

## Overview

This is the IDBT (Inisiatif Data Beneran Terbuka) repository — an open data store for Indonesian economic statistics from BPS (Badan Pusat Statistik) PDF publications. Data is stored as Parquet files and served via DuckDB-WASM on GitHub Pages.

## Directory Layout

- inbox/ — User drops clean CSVs here for ingestion
- archive/ — Ingested CSVs are moved here with a timestamp prefix
- data/ref/ — Reference Parquet tables (geography, indicators, publications)
- data/facts/ — Fact Parquet tables (statistical data in long format)
- seeds/ — CSV source files for regenerating reference tables
- scripts/ — Python helper scripts (ingest.py, validate.py, init_refs.py, export_csv.py)
- site/ — GitHub Pages frontend (DuckDB-WASM query interface)

## Schemas

### Fact tables (data/facts/*.parquet)

Every fact table uses this long format:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| kode_wilayah | str | conditional | BPS region code. Present when data is by geography. |
| kbli | str | conditional | KBLI industrial classification code. Present when data is by industry. |
| tahun | int | yes | Reference year |
| indikator_id | str | yes | Maps to ref_indikator |
| nilai | float | yes | The numeric value |
| publikasi_id | str | yes | Maps to ref_publikasi |

At least one of kode_wilayah or kbli must be present. Not both unless the data is cross-tabulated by geography AND industry.

### ref_wilayah (data/ref/ref_wilayah.parquet)

Columns: kode_wilayah (str), nama_wilayah (str), tingkat (str), kode_provinsi (str)

### ref_pemekaran (data/ref/ref_pemekaran.parquet)

Columns: kode_induk (str), kode_baru (str), tahun_efektif (int)

### ref_publikasi (data/ref/ref_publikasi.parquet)

Columns: publikasi_id (str), judul (str), seri (str), tahun (int), provinsi (str), url_sumber (str)

### ref_indikator (data/ref/ref_indikator.parquet)

Columns: indikator_id (str), nama_id (str), nama_en (str), satuan (str), seri (str), catatan (str)

## Ingestion Workflow

When the user says "ingest", "process inbox", or similar, follow these steps:

### Step 1: Discover

```python
from scripts.ingest import *
files = list_inbox()
```

If no files, say so and stop. Otherwise list them.

### Step 2: For each CSV file

a) Preview it:

```python
preview_csv(path)
meta = parse_filename(path)  # gives domain, dimension, year
```

Show the user the preview and parsed metadata. Ask if it looks correct.

b) Identify indicators. Look at the value columns (non-key, non-tahun columns). For each one:
- Check if a matching indikator_id already exists in ref_indikator (search by nama_id or by similar column name)
- If not, propose a new indikator_id following the pattern: uppercase domain abbreviation + 3-digit number, e.g., IND001, IND002, KTK001
- Ask the user to confirm the indikator_id, nama_id (Indonesian), nama_en (English), and satuan for each new indicator
- Register confirmed indicators using register_indikator()

c) Check publication. Using the parsed year and domain:
- Check if a matching publikasi_id exists in ref_publikasi
- If not, ask the user for: judul, seri, tahun, provinsi
- Register it using register_publikasi()

d) Validate:

```python
# If dimension is geographic (provinsi, kabupaten):
invalid = validate_wilayah(df)
# If invalid codes found, report them and ask user how to proceed
```

e) Build the indicator mapping and transform:

```python
indikator_mapping = {
    "column_name_in_csv": "IND001",
    "another_column": "IND002",
}
long_df = to_long_format(df, key_col, tahun, value_columns, indikator_mapping, publikasi_id)
```

f) Check for duplicates against existing data:

```python
dupes = validate_no_duplicates(long_df, target_path)
```

If duplicates found, warn the user and ask whether to skip duplicates or abort.

g) Append:

```python
append_to_parquet(long_df, f"data/facts/{meta['domain']}.parquet")
```

h) Archive:

```python
archive_csv(path)
```

### Step 3: Report

Print a summary:
- Number of files processed
- Number of rows added per file
- Which fact tables were updated
- Which new indicators were registered

### Step 4: Commit

Run: git add -A
Suggest a commit message like: "data: ingest {domain} {year} from {publication}"

## Validation

Run at any time with: python scripts/validate.py

## Key Rules

- kode_wilayah and kbli are ALWAYS strings, never integers (preserve leading zeros)
- Indonesian number format uses dots as thousands separators — CSVs in inbox must already have these removed
- Values in "000 Rp" means thousands of Rupiah — store the number as-is, record the unit in ref_indikator.satuan
- tahun is always an integer between 1970 and current year
- When in doubt about indicator mappings or publication details, ASK the user

## Useful Commands

```bash
python scripts/init_refs.py              # Rebuild reference tables from seeds
python scripts/validate.py               # Validate all Parquet files
python scripts/validate.py path.parquet  # Validate one file
python scripts/export_csv.py path.parquet # Print Parquet as CSV
python -c "import pandas as pd; print(pd.read_parquet('data/facts/industri.parquet'))"
```
