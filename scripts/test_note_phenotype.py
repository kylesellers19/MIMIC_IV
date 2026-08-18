#!/usr/bin/env python3
"""Unit tests for the note phenotype rule (synthetic strings only — no patient data).

Covers the v1.1.0 required cases plus the v1.0.0 suite updated for the bare-`fatty`
removal and fatty-infiltration tightening. Run: python scripts/test_note_phenotype.py
"""
from scripts.note_phenotype import classify_note, VERSION

# (label, text, expect_a_pos, expect_tierC)
CASES = [
    # --- v1.1.0 REQUIRED ---
    ("free fatty acids must NOT fire",            "Elevated free fatty acids on the panel.", False, False),
    ("omega-3 fatty acids must NOT fire",         "Continue omega-3 fatty acids supplement.", False, False),
    ("fatty replacement of pancreas NOT fire",    "There is fatty replacement of the pancreas.", False, False),
    ("fatty replacement of liver MUST fire",      "There is fatty replacement of the liver.", True, False),
    ("hepatic steatosis still fires",             "Compatible with hepatic steatosis.", True, False),
    ("no evidence of hepatic steatosis NOT fire", "No evidence of hepatic steatosis.", False, False),
    # --- core positives ---
    ("stem steatosis scoped to liver",            "Moderate steatosis of the liver.", True, False),
    ("NASH fires",                                "Known history is significant for NASH.", True, False),
    ("fatty liver phrase fires",                  "Ultrasound shows fatty liver.", True, False),
    ("fatty deposition in liver (strict) fires",  "Focal fatty deposition within the liver.", True, False),
    ("fatty infiltrate of liver (strict) fires",  "Fatty infiltrate of the hepatic parenchyma.", True, False),
    # --- context / negation / family / historical ---
    ("negated fatty change in liver NOT fire",    "No fatty change in the liver.", False, False),
    ("family history NASH NOT fire",              "Family history of NASH in her mother.", False, False),
    ("historical NAFLD still positive",           "History of NAFLD; liver stable.", True, False),
    ("hedged -> Tier C not A",                    "Findings concerning for hepatic steatosis.", False, True),
    ("pseudo-neg not negated",                    "No significant change; hepatic steatosis again seen.", True, False),
    # --- anatomical suppression ---
    ("fatty infiltration of pancreas NOT fire",   "Fatty infiltration of the pancreas.", False, False),
    ("marrow suppressed",                         "Fatty marrow signal in vertebrae.", False, False),
    # --- bare fatty removed in v1.1.0 ---
    ("bare fatty near liver now NOT fire",        "The liver is fatty and enlarged.", False, False),
    # --- fatty infiltration tightened: no liver token -> NOT fire ---
    ("fatty infiltration no-liver NOT fire",      "Fatty infiltration noted throughout.", False, False),
    ("fatty infiltration of liver fires",         "Fatty infiltration of the liver.", True, False),
    # --- fatty sparing kept standard: clean sentence still fires ---
    ("fatty sparing clean sentence fires",        "Focal fatty sparing near the porta.", True, False),
    # --- Tier B ---
    ("Tier B echogenic liver (B not A)",          "Increased hepatic echogenicity noted.", False, False),
]

print(f"note_phenotype VERSION {VERSION} — unit tests\n")
npass = 0
for label, txt, exp_a, exp_c in CASES:
    r = classify_note(txt)
    ok = (r["a_pos"] == exp_a) and (r["c_hedged"] == exp_c)
    npass += ok
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:44s} A={int(r['a_pos'])}(exp {int(exp_a)}) "
          f"C={int(r['c_hedged'])}(exp {int(exp_c)})")
print(f"\n{npass}/{len(CASES)} passed")
if npass != len(CASES):
    raise SystemExit(1)
