#!/usr/bin/env python3
"""STEP 2d — audit the anatomical-scoping fallback across all Tier A triggers.

For every Tier A trigger, count affirmed-positive hits that passed via
AFFIRMATIVE liver/hepatic evidence vs ONLY via the 'no competing organ'
fallback. Uses the shared _iter_hits() from the rule module (no reimplementation).
Read-only; aggregate only. Scope = inpatient-linked notes on the locked population.

Run: python scripts/scoping_audit.py
"""
from collections import defaultdict, Counter

import duckdb
from scripts.note_phenotype import _iter_hits, NOTE, POP, VERSION, TRIGGERS

con = duckdb.connect(); con.execute("SET memory_limit='24GB'")
locked_hadm = set(con.execute(
    f"SELECT hadm_id FROM read_parquet('{POP}')").fetchdf().hadm_id.astype("int64"))

tally = defaultdict(Counter)   # trigger name -> Counter(reason)
scope_of = {name: scope for name, _rx, tier, scope in TRIGGERS}

def run(table):
    reader = con.execute(
        f"SELECT hadm_id, text FROM read_csv_auto('{NOTE}/{table}.csv.gz')"
    ).fetch_record_batch(3000)
    for batch in reader:
        d = batch.to_pydict()
        for k in range(len(d["text"])):
            h = d["hadm_id"][k]
            if h is None or int(h) not in locked_hadm:
                continue
            for hit in _iter_hits(d["text"][k]):
                if hit["disp"] == "positive" and hit["tier"] == "A":
                    tally[hit["name"]][hit.get("reason", "none")] += 1

print(f"scoping_audit (rule v{VERSION}); scope = inpatient-linked notes")
print("scanning discharge ..."); run("discharge")
print("scanning radiology ..."); run("radiology")

print("\n== Tier A trigger fallback audit (positive hits) ==")
print(f"{'trigger':34s} {'scope':9s} {'affirm':>8s} {'fallback':>9s} {'none':>7s} {'%fallback':>10s}")
ambiguous_flag = []
RULED = {"fatty replacement", "fatty deposition", "fatty degeneration",
         "fatty metamorphosis", "fatty infiltrate"}  # already strict in v1.1.0
SELF_HEPATIC_STEMS = {"steatosis", "steatotic", "steatohepatitis"}  # researcher: no decision needed
for name, _rx, tier, scope in TRIGGERS:
    if tier != "A":
        continue
    c = tally.get(name, Counter())
    aff = c.get("affirmative", 0); fb = c.get("fallback", 0); nn = c.get("none", 0)
    tot_scoped = aff + fb
    pctfb = (100 * fb / tot_scoped) if tot_scoped else 0.0
    print(f"{name:34s} {scope:9s} {aff:>8,} {fb:>9,} {nn:>7,} {pctfb:>9.1f}%")
    # flag non-ruled, non-self-hepatic STANDARD triggers with material fallback
    if scope == "standard" and name not in SELF_HEPATIC_STEMS and fb > 0:
        ambiguous_flag.append((name, aff, fb, pctfb))

print("\n== STOP-CHECK: organ-ambiguous STANDARD triggers relying on fallback ==")
if ambiguous_flag:
    for name, aff, fb, pctfb in ambiguous_flag:
        print(f"  {name}: affirmative={aff:,} fallback={fb:,} ({pctfb:.1f}% via fallback)")
    print("  -> These are NOT among the triggers the researcher ruled on. Per Step 2d, "
          "STOP and ask before changing their scoping.")
else:
    print("  none — no organ-ambiguous standard trigger relies on the fallback.")
