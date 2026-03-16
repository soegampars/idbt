# Inbox — CSV Drop Zone

Place clean CSV files here for ingestion into the IDBT database.

## Filename convention

`{domain}_{dimension}_{year}.csv`

- **domain**: Target fact table name. Examples: `industri`, `ketenagakerjaan`, `penduduk`, `pdrb`
- **dimension**: What the rows represent. Examples: `kbli`, `provinsi`, `kabupaten`
- **year**: Reference year of the data. Example: `2013`

Full example: `industri_kbli_2013.csv`

## Required columns

Your CSV must contain:

- A key column: either `kode_wilayah` (BPS region code as string) or `kbli` (industrial classification code)
- Optionally a `tahun` column (if absent, year is taken from the filename)
- One or more numeric value columns with descriptive headers

## Number format

- Use plain integers or decimals: `528795277` not `528.795.277`
- Indonesian dot-as-thousands must be removed before placing here
- Decimal separator is a period: `3.14`
- Missing values: leave the cell empty (not "NA", not "-", not "0" unless actually zero)

## Encoding

UTF-8 only.

## Example

Filename: `industri_kbli_2013.csv`

```csv
kbli,tahun,jumlah_perusahaan,pekerja_produksi_total,pekerja_lain_total,pekerja_total
10/11,2013,40,5254,2242,7496
12,2013,7,3758,384,4142
13,2013,28,7593,811,8404
```

After ingestion, the CSV will be moved to `archive/` automatically.
