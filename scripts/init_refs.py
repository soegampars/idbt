"""Read CSV seeds and write Parquet reference tables to data/ref/."""

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SEEDS_DIR = REPO_ROOT / "seeds"
REF_DIR = REPO_ROOT / "data" / "ref"

DTYPE_OVERRIDES = {
    "ref_wilayah": {"kode_wilayah": str, "kode_provinsi": str},
    "ref_pemekaran": {"kode_induk": str, "kode_baru": str},
}


def main():
    REF_DIR.mkdir(parents=True, exist_ok=True)

    for csv_path in sorted(SEEDS_DIR.glob("*.csv")):
        name = csv_path.stem
        dtype = DTYPE_OVERRIDES.get(name)
        df = pd.read_csv(csv_path, dtype=dtype)

        out_path = REF_DIR / f"{name}.parquet"
        df.to_parquet(out_path, engine="pyarrow", index=False)
        print(f"Created data/ref/{name}.parquet — {len(df)} rows")


if __name__ == "__main__":
    main()
