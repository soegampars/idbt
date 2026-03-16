"""Export Parquet files as CSV for inspection.

Usage:
    python scripts/export_csv.py data/facts/industri.parquet              # stdout
    python scripts/export_csv.py data/facts/industri.parquet output.csv   # file
    python scripts/export_csv.py --all                                     # export all
"""

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
EXPORT_DIR = Path("/tmp/idbt_export")


def export_one(parquet_path, csv_path=None):
    df = pd.read_parquet(parquet_path)
    if csv_path is None:
        sys.stdout.write(df.to_csv(index=False))
    else:
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"Exported {csv_path} ({len(df)} rows)")


def export_all():
    for parquet_path in sorted(DATA_DIR.rglob("*.parquet")):
        rel = parquet_path.relative_to(DATA_DIR)
        csv_path = EXPORT_DIR / rel.with_suffix(".csv")
        export_one(parquet_path, csv_path)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)
    if sys.argv[1] == "--all":
        export_all()
    elif len(sys.argv) == 2:
        export_one(sys.argv[1])
    else:
        export_one(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
