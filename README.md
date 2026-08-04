# MASLD / MIMIC-IV Phenotyping — Local Data Layer

Local DuckDB tooling for a cross-sectional MASLD (metabolic dysfunction–associated
steatotic liver disease) phenotyping study on MIMIC-IV.

The approach: **query the gzipped CSVs directly with DuckDB** (no full import),
filter down to a cohort, then **materialize the filtered subset to Parquet** for
fast iterative joins. With ~32 GB RAM this avoids ever loading the large event
tables (e.g. `labevents`) into memory in full.

## Status

Tooling only. **No data is downloaded** — PhysioNet credentialing pending.

## Datasets (once credentialed)

Download these from PhysioNet into `data/raw/` (see layout below):

- **MIMIC-IV** (`hosp/`, `icu/` modules) — demographics, admissions, diagnoses, labs
- **MIMIC-IV-Note** (`note/`) — discharge & radiology free text (for NLP phenotyping)
- **MIMIC-IV-ED** (`ed/`) — emergency department stays

Keep files **gzipped** (`*.csv.gz`); DuckDB reads them compressed.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # duckdb python bindings
python -c "import duckdb; print(duckdb.__version__)"   # verify

duckdb --version                          # CLI (installed via: brew install duckdb)
```

## Project layout

```
masld_mimic/
├── data/                 # gitignored — never committed (credentialed data)
│   ├── raw/              # downloaded MIMIC files, keep gzipped, mirror PhysioNet tree:
│   │   ├── mimiciv/hosp/*.csv.gz
│   │   ├── mimiciv/icu/*.csv.gz
│   │   ├── mimic-iv-note/note/*.csv.gz
│   │   └── mimic-iv-ed/ed/*.csv.gz
│   └── processed/        # derived Parquet (cohort subsets, feature tables)
├── sql/                  # reusable SQL queries
│   └── cohort_example.sql
├── scripts/              # python helpers
│   └── materialize_cohort.py
├── notebooks/            # exploratory analysis
├── requirements.txt
└── README.md
```

## Querying MIMIC CSVs directly (no import)

DuckDB reads gzipped CSVs in place. `read_csv_auto` sniffs types; for the big
MIMIC tables it's worth being explicit where the sniffer guesses wrong (e.g.
ICD codes are strings, not numbers).

CLI:

```bash
duckdb   # in-memory session
```
```sql
-- one-off scan of a compressed table
SELECT count(*) FROM read_csv_auto('data/raw/mimiciv/hosp/patients.csv.gz');

-- give a table a short alias for the session (a VIEW, not a copy)
CREATE VIEW patients   AS SELECT * FROM read_csv_auto('data/raw/mimiciv/hosp/patients.csv.gz');
CREATE VIEW admissions AS SELECT * FROM read_csv_auto('data/raw/mimiciv/hosp/admissions.csv.gz');
CREATE VIEW diagnoses  AS SELECT * FROM read_csv_auto('data/raw/mimiciv/hosp/diagnoses_icd.csv.gz');

SELECT p.gender, count(*) FROM patients p GROUP BY 1;
```

Python (same idea):

```python
import duckdb
con = duckdb.connect()        # in-memory; or duckdb.connect("data/processed/masld.duckdb")
con.sql("""
  SELECT count(*) AS n
  FROM read_csv_auto('data/raw/mimiciv/hosp/diagnoses_icd.csv.gz')
""").show()
```

Why this works well here: only the columns/rows you touch are decompressed and
scanned. Pushdown means `WHERE icd_code IN (...)` on `diagnoses_icd` never
materializes the whole table.

### Forcing column types (recommended for codes/IDs)

```sql
SELECT * FROM read_csv(
  'data/raw/mimiciv/hosp/diagnoses_icd.csv.gz',
  types = {'icd_code': 'VARCHAR', 'icd_version': 'INTEGER',
           'subject_id': 'BIGINT', 'hadm_id': 'BIGINT'}
);
```

## Materializing a cohort subset to Parquet

Cohort-extraction-then-join pattern: identify subjects once (scanning the big
tables), write the filtered slices to Parquet in `data/processed/`, then do all
downstream work against the small Parquet files.

```sql
-- 1. define the cohort (example: any liver-steatosis-related ICD code)
COPY (
  SELECT DISTINCT subject_id
  FROM read_csv_auto('data/raw/mimiciv/hosp/diagnoses_icd.csv.gz')
  WHERE icd_code LIKE 'K76%'      -- ICD-10 fatty liver / NAFLD family (refine for your phenotype)
     OR icd_code LIKE '5715%'     -- ICD-9 equivalents
) TO 'data/processed/cohort_ids.parquet' (FORMAT parquet);

-- 2. write the filtered slice of a big table, keeping only cohort rows
COPY (
  SELECT l.*
  FROM read_csv_auto('data/raw/mimiciv/hosp/labevents.csv.gz') l
  SEMI JOIN read_parquet('data/processed/cohort_ids.parquet') c
    ON l.subject_id = c.subject_id
) TO 'data/processed/cohort_labevents.parquet' (FORMAT parquet);
```

Then iterate cheaply:

```sql
SELECT * FROM read_parquet('data/processed/cohort_labevents.parquet')
WHERE itemid IN (50861 /* ALT */, 50878 /* AST */);
```

Parquet keeps types, is columnar, and is far faster to re-scan than the gzipped
CSVs. Partition large outputs with
`(FORMAT parquet, PARTITION_BY (subject_id_bucket))` if a single file gets unwieldy.

See [sql/cohort_example.sql](sql/cohort_example.sql) for a runnable template and
[scripts/materialize_cohort.py](scripts/materialize_cohort.py) for the Python version.

## Memory tips (32 GB box)

- Cap DuckDB if you run other things: `SET memory_limit='24GB';`
- DuckDB spills to disk when it must; set `SET temp_directory='data/processed/tmp';`
- Prefer `SEMI JOIN` / `WHERE ... IN (subquery)` to filter big tables by the
  cohort rather than full joins.
- Never `SELECT *` a big table into a pandas DataFrame — keep it in DuckDB or
  write to Parquet first.

## Data safety

`data/` is gitignored in full (only `.gitkeep` placeholders are tracked).
Credentialed PhysioNet data must never be committed. Confirm before any push:

```bash
git status --porcelain data/   # should show nothing but .gitkeep files
```
