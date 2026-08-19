#!/usr/bin/env python3
"""STEP 5 — clustering & comorbidity burden.

Subjects per #admissions; cross-cell subjects among code-/note+; Charlson
Comorbidity Index by cell with SMDs. Charlson computed from the Quan et al.
(2005) ICD-9-CM/ICD-10 coding algorithm (Med Care 43:1130) with standard
hierarchy rules and Charlson (1987) weights. Aggregate only. Writes frag_step5.md.

Run: python scripts/comorbid_cluster.py
"""
import os
import numpy as np
import pandas as pd
import duckdb
from scripts.masld_config import DATA

FRAG = os.path.join(os.environ.get("SCRATCH", "/tmp"), "frag_step5.md")
con = duckdb.connect(); con.execute("SET memory_limit='24GB'")

# Quan 2005 crosswalk: category -> (weight, icd10 prefixes, icd9 prefixes)
CH = {
  "mi": (1, ["I21", "I22", "I252"], ["410", "412"]),
  "chf": (1, ["I099", "I110", "I130", "I132", "I255", "I420", "I425", "I426", "I427",
              "I428", "I429", "I43", "I50", "P290"],
          ["39891", "40201", "40211", "40291", "40401", "40403", "40411", "40413",
           "40491", "40493", "4254", "4255", "4256", "4257", "4258", "4259", "428"]),
  "pvd": (1, ["I70", "I71", "I731", "I738", "I739", "I771", "I790", "I792", "K551",
              "K558", "K559", "Z958", "Z959"],
          ["0930", "4373", "440", "441", "4431", "4432", "4433", "4434", "4435", "4436",
           "4437", "4438", "4439", "4471", "5571", "5579", "V434"]),
  "cevd": (1, ["G45", "G46", "H340", "I60", "I61", "I62", "I63", "I64", "I65", "I66",
               "I67", "I68", "I69"], ["36234", "430", "431", "432", "433", "434", "435",
               "436", "437", "438"]),
  "dementia": (1, ["F00", "F01", "F02", "F03", "F051", "G30", "G311"], ["290", "2941", "3312"]),
  "copd": (1, ["I278", "I279", "J40", "J41", "J42", "J43", "J44", "J45", "J46", "J47",
               "J60", "J61", "J62", "J63", "J64", "J65", "J66", "J67", "J684", "J701", "J703"],
           ["4168", "4169", "490", "491", "492", "493", "494", "495", "496", "497", "498",
            "499", "500", "501", "502", "503", "504", "505", "5064", "5081", "5088"]),
  "rheum": (1, ["M05", "M06", "M315", "M32", "M33", "M34", "M351", "M353", "M360"],
            ["4465", "7100", "7101", "7102", "7103", "7104", "7140", "7141", "7142", "7148", "725"]),
  "pud": (1, ["K25", "K26", "K27", "K28"], ["531", "532", "533", "534"]),
  "mild_liver": (1, ["B18", "K700", "K701", "K702", "K703", "K709", "K713", "K714", "K715",
                     "K717", "K73", "K74", "K760", "K762", "K763", "K764", "K768", "K769", "Z944"],
                 ["07022", "07023", "07032", "07033", "07044", "07054", "0706", "0709",
                  "570", "571", "5733", "5734", "5738", "5739", "V427"]),
  "dm": (1, ["E100", "E101", "E106", "E108", "E109", "E110", "E111", "E116", "E118", "E119",
             "E120", "E121", "E126", "E128", "E129", "E130", "E131", "E136", "E138", "E139",
             "E140", "E141", "E146", "E148", "E149"],
         ["2500", "2501", "2502", "2503", "2508", "2509"]),
  "dm_comp": (2, ["E102", "E103", "E104", "E105", "E107", "E112", "E113", "E114", "E115",
                  "E117", "E122", "E123", "E124", "E125", "E127", "E132", "E133", "E134",
                  "E135", "E137", "E142", "E143", "E144", "E145", "E147"],
              ["2504", "2505", "2506", "2507"]),
  "hemi": (2, ["G041", "G114", "G801", "G802", "G81", "G82", "G830", "G831", "G832", "G833",
               "G834", "G839"], ["3341", "342", "343", "3440", "3441", "3442", "3443", "3444",
               "3445", "3446", "3449"]),
  "renal": (2, ["I120", "I131", "N032", "N033", "N034", "N035", "N036", "N037", "N052", "N053",
                "N054", "N055", "N056", "N057", "N18", "N19", "N250", "Z490", "Z491", "Z492",
                "Z940", "Z992"], ["40301", "40311", "40391", "40402", "40403", "40412", "40413",
                "40492", "40493", "582", "5830", "5831", "5832", "5833", "5834", "5835", "5836",
                "5837", "585", "586", "5880", "V420", "V451", "V56"]),
  "malig": (2, ["C0", "C1", "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C30", "C31",
                "C32", "C33", "C34", "C37", "C38", "C39", "C40", "C41", "C43", "C45", "C46",
                "C47", "C48", "C49", "C5", "C60", "C61", "C62", "C63", "C64", "C65", "C66",
                "C67", "C68", "C69", "C70", "C71", "C72", "C73", "C74", "C75", "C76", "C81",
                "C82", "C83", "C84", "C85", "C88", "C90", "C91", "C92", "C93", "C94", "C95",
                "C96", "C97"], ["14", "15", "16", "170", "171", "172", "174", "175", "176",
                "179", "18", "190", "191", "192", "193", "194", "1950", "1951", "1952", "1953",
                "1954", "1955", "1956", "1957", "1958", "200", "201", "202", "203", "204",
                "205", "206", "207", "208", "2386"]),
  "severe_liver": (3, ["I850", "I859", "I864", "I982", "K704", "K711", "K721", "K729", "K765",
                       "K766", "K767"], ["4560", "4561", "4562", "5722", "5723", "5724", "5725",
                       "5726", "5727", "5728"]),
  "mets": (6, ["C77", "C78", "C79", "C80"], ["196", "197", "198", "199"]),
  "hiv": (6, ["B20", "B21", "B22", "B24"], ["042", "043", "044"]),
}

def rex(prefixes):
    return "^(" + "|".join(prefixes) + ")"

sel = []
for cat, (wt, p10, p9) in CH.items():
    sel.append(f"max(CASE WHEN (icd_version=10 AND regexp_matches(code,'{rex(p10)}')) "
               f"OR (icd_version=9 AND regexp_matches(code,'{rex(p9)}')) THEN 1 ELSE 0 END) AS {cat}")
cats = con.execute(f"""
  WITH d AS (SELECT hadm_id, trim(icd_code) AS code, icd_version
             FROM read_csv('{DATA}/diagnoses_icd.csv.gz', types={{'icd_code':'VARCHAR'}}))
  SELECT hadm_id, {', '.join(sel)} FROM d GROUP BY hadm_id
""").fetchdf().set_index("hadm_id")

# hierarchy: comp>dm, severe>mild liver, mets>malig
cats.loc[cats.dm_comp == 1, "dm"] = 0
cats.loc[cats.severe_liver == 1, "mild_liver"] = 0
cats.loc[cats.mets == 1, "malig"] = 0
cats["charlson"] = sum(CH[c][0] * cats[c] for c in CH)

frame = con.execute("""SELECT hadm_id, subject_id, code_positive, note_b
    FROM read_parquet('data/processed/aim1a_frame.parquet')""").fetchdf()
frame["cell"] = frame.apply(lambda r: ("code+" if r.code_positive else "code-") +
                            ("/note+" if r.note_b else "/note-"), axis=1)
frame = frame.merge(cats["charlson"], left_on="hadm_id", right_index=True, how="left")

L = []
def w(s=""): L.append(s)
w("## Step 5 — Clustering & comorbidity burden\n")

# subjects per #admissions
sadm = frame.groupby("subject_id").size()
def bucket(n):
    return "1" if n == 1 else "2" if n == 2 else "3-5" if n <= 5 else "6+"
b = sadm.map(bucket).value_counts()
w("### Subjects by number of admissions contributed\n")
w("| admissions | subjects | % |"); w("| --- | --: | --: |")
for k in ["1", "2", "3-5", "6+"]:
    w(f"| {k} | {int(b.get(k,0)):,} | {100*b.get(k,0)/len(sadm):.1f}% |")
w("")

# code-/note+ subjects crossing cells
rz = frame[frame.cell == "code-/note+"]
rz_subj = set(rz.subject_id)
sub_cells = frame[frame.subject_id.isin(rz_subj)].groupby("subject_id")
cross = sum(1 for _, g in sub_cells if set(g.cell) - {"code-/note+"})
code_flip = sum(1 for _, g in sub_cells if g.code_positive.nunique() > 1)
w("### Coding inconsistency among code−/note+ subjects\n")
w(f"- code−/note+ admissions: {len(rz):,} across **{len(rz_subj):,} subjects**.")
w(f"- Subjects with ≥1 OTHER admission in a different cell: **{cross:,} "
  f"({100*cross/len(rz_subj):.1f}%)**.")
w(f"- Subjects whose **coding status changes** across stays (code+ on some admission, "
  f"code− on another): **{code_flip:,} ({100*code_flip/len(rz_subj):.1f}%)** — directly "
  f"informative about coding inconsistency.\n")

# Charlson by cell
def smd_cont(a, b):
    a, b = a.dropna(), b.dropna()
    d = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    return np.nan if d == 0 else (a.mean() - b.mean()) / d
w("### Charlson Comorbidity Index by 2×2 cell (Quan 2005 crosswalk, Charlson weights)\n")
w("| cell | n | mean | median [IQR] | SMD vs code+/note+ |")
w("| --- | --: | --: | --- | --: |")
ref = frame[frame.cell == "code+/note+"].charlson
for cell in ["code+/note+", "code-/note+", "code+/note-", "code-/note-"]:
    g = frame[frame.cell == cell].charlson
    smd = "" if cell == "code+/note+" else f"{smd_cont(g, ref):+.3f}"
    w(f"| {cell} | {len(g):,} | {g.mean():.2f} | "
      f"{g.median():.0f} [{g.quantile(.25):.0f}, {g.quantile(.75):.0f}] | {smd} |")
w("")

os.makedirs(os.path.dirname(FRAG), exist_ok=True)
with open(FRAG, "w") as fh:
    fh.write("\n".join(L) + "\n")
print(f"wrote {FRAG}")
print(f"code-/note+ subjects={len(rz_subj):,} cross-cell={cross:,} code-flip={code_flip:,}")
print("Charlson by cell mean:", {c: round(frame[frame.cell==c].charlson.mean(),2)
      for c in ['code+/note+','code-/note+','code+/note-','code-/note-']})
