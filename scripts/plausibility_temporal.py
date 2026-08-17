#!/usr/bin/env python3
"""STEP 3 — PLAUSIBILITY tests, temporal (Kahn et al. 2016 DQ framework).

Ordering/interval checks with counts and small samples. Read-only; nothing
deleted. Checks 4-5 (labevents, non-null hadm_id) are computed over ALL such
labs and share a single scan; that scope is stated in output.

Run: python scripts/plausibility_temporal.py
"""
import duckdb
from scripts.masld_config import DATA

con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
con.execute(f"""
CREATE TEMP VIEW adm AS
  SELECT a.subject_id, a.hadm_id, a.admittime, a.dischtime, a.deathtime,
         a.admission_type, p.dod, p.anchor_year_group
  FROM read_csv_auto('{DATA}/admissions.csv.gz') a
  JOIN read_csv_auto('{DATA}/patients.csv.gz') p USING (subject_id);
""")

print("=" * 72)
print("3.1  admittime > dischtime  (negative LOS)")
print("=" * 72)
tot = con.execute("SELECT count(*) FROM adm WHERE admittime > dischtime").fetchone()[0]
subj = con.execute("SELECT count(DISTINCT subject_id) FROM adm WHERE admittime > dischtime").fetchone()[0]
print(f"  total: {tot:,}   distinct subjects: {subj:,}")
print("  by anchor_year_group:")
print(con.execute("""
  SELECT anchor_year_group, count(*) n FROM adm WHERE admittime>dischtime
  GROUP BY 1 ORDER BY n DESC""").fetchdf().to_string(index=False))
print("  by admission_type:")
print(con.execute("""
  SELECT admission_type, count(*) n FROM adm WHERE admittime>dischtime
  GROUP BY 1 ORDER BY n DESC""").fetchdf().to_string(index=False))
print("  sample:")
print(con.execute("""
  SELECT subject_id,hadm_id,admittime,dischtime,
         date_diff('hour',admittime,dischtime) AS hours
  FROM adm WHERE admittime>dischtime ORDER BY hours LIMIT 5""").fetchdf().to_string(index=False))

print("\n" + "=" * 72)
print("3.2  deathtime outside [admittime, dischtime]")
print("=" * 72)
r = con.execute("""
  SELECT count(*) FILTER (WHERE deathtime IS NOT NULL) AS n_deathtime,
         count(*) FILTER (WHERE deathtime IS NOT NULL
                          AND (deathtime < admittime OR deathtime > dischtime)) AS outside
  FROM adm""").fetchone()
print(f"  admissions with deathtime: {r[0]:,}   outside interval: {r[1]:,}")
print(con.execute("""
  SELECT subject_id,hadm_id,admittime,dischtime,deathtime FROM adm
  WHERE deathtime IS NOT NULL AND (deathtime<admittime OR deathtime>dischtime)
  LIMIT 5""").fetchdf().to_string(index=False))

print("\n" + "=" * 72)
print("3.3  dischtime after dod (discharge after date of death)")
print("=" * 72)
# dod is a DATE; compare against dischtime date. Flag discharge strictly after dod.
r = con.execute("""
  SELECT count(*) FILTER (WHERE dod IS NOT NULL AND dischtime::DATE > dod) AS n
  FROM adm""").fetchone()
print(f"  dischtime date after dod: {r[0]:,}")
print(con.execute("""
  SELECT subject_id,hadm_id,dischtime,dod FROM adm
  WHERE dod IS NOT NULL AND dischtime::DATE > dod
  ORDER BY dischtime::DATE - dod DESC LIMIT 5""").fetchdf().to_string(index=False))

print("\n" + "=" * 72)
print("3.4 + 3.5  labevents temporal (ALL labs; charttime window needs non-null hadm_id)")
print("=" * 72)
r = con.execute(f"""
  WITH a AS (SELECT hadm_id, admittime, dischtime
             FROM read_csv_auto('{DATA}/admissions.csv.gz'))
  SELECT
    count(*)                                                       AS total_rows,
    count(*) FILTER (WHERE l.storetime IS NOT NULL AND l.charttime IS NOT NULL
                     AND l.storetime < l.charttime)                AS store_before_chart,
    count(*) FILTER (WHERE l.hadm_id IS NOT NULL)                  AS linked_rows,
    count(*) FILTER (WHERE l.hadm_id IS NOT NULL AND a.hadm_id IS NOT NULL
                     AND (l.charttime < a.admittime
                          OR l.charttime > a.dischtime))           AS chart_outside_window
  FROM read_csv_auto('{DATA}/labevents.csv.gz') l
  LEFT JOIN a USING (hadm_id)
""").fetchone()
print(f"  total lab rows                         : {r[0]:,}")
print(f"  storetime < charttime (impossible order): {r[1]:,}")
print(f"  linked rows (hadm_id not null)         : {r[2]:,}")
print(f"  charttime outside [admit,disch] window : {r[3]:,}  "
      f"({100*r[3]/r[2]:.2f}% of linked)")

print("\n" + "=" * 72)
print("3.6  omr chartdate vs subject admissions / death")
print("=" * 72)
r = con.execute(f"""
  WITH o AS (SELECT DISTINCT subject_id, chartdate
             FROM read_csv_auto('{DATA}/omr.csv.gz')),
       span AS (SELECT subject_id, min(admittime::DATE) first_adm,
                       max(dischtime::DATE) last_disch
                FROM read_csv_auto('{DATA}/admissions.csv.gz') GROUP BY 1),
       pat AS (SELECT subject_id, dod FROM read_csv_auto('{DATA}/patients.csv.gz'))
  SELECT
    count(*)                                                    AS omr_subject_dates,
    count(*) FILTER (WHERE pat.dod IS NOT NULL AND o.chartdate > pat.dod) AS after_death,
    count(*) FILTER (WHERE span.subject_id IS NULL)             AS subject_no_admission,
    count(*) FILTER (WHERE span.subject_id IS NOT NULL
                     AND (o.chartdate < span.first_adm OR o.chartdate > span.last_disch)) AS outside_adm_span
  FROM o
  LEFT JOIN span USING (subject_id)
  LEFT JOIN pat  USING (subject_id)
""").fetchone()
print(f"  distinct (subject, omr chartdate)     : {r[0]:,}")
print(f"  omr chartdate AFTER dod (impossible)  : {r[1]:,}")
print(f"  omr for subject with no admission     : {r[2]:,}")
print(f"  omr chartdate outside admission span  : {r[3]:,}  "
      f"(expected: omr is outpatient)")
