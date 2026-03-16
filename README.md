# IDBT — Inisiatif Data (Beneran) Terbuka

An open data initiative providing free, structured access to Indonesian economic statistics originally published in PDF format by [BPS](https://www.bps.go.id/) (Badan Pusat Statistik / Statistics Indonesia).

## What this is

BPS publishes thousands of statistical tables every year, but most are locked inside PDF documents that are difficult to use programmatically. This repository:

- Extracts and cleans that data into structured Parquet files
- Provides a browser-based query interface (no downloads or tools required)
- Lets users select exactly the variables, regions, and years they need
- Exports clean CSV files ready for analysis in Excel, Stata, R, or Python

## How data is organised

All data follows a consistent long format with geographic or classification keys, linked to reference tables for region names, indicator definitions, and source publications. See `CLAUDE.md` for full schema documentation.

## How to access the data

Visit the GitHub Pages site at `https://[username].github.io/idbt/` to query and download data directly in your browser. No account or software needed.

## How to contribute

If you have access to BPS publications and want to help expand the dataset:

1. Extract the table into a clean CSV (see `inbox/README.md` for format conventions)
2. Submit a pull request placing your CSV in the `inbox/` folder
3. Include the source publication details in your PR description

## Tech stack

- **Storage**: Apache Parquet on GitHub
- **Query engine**: DuckDB-WASM (runs entirely in the browser)
- **Ingestion**: Python (pandas + pyarrow), managed via Claude Code
- **Frontend**: Static HTML/JS on GitHub Pages

## License

Data sourced from BPS publications which are public domain under Indonesian law. Code in this repository is MIT licensed.
