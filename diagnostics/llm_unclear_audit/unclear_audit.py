#!/usr/bin/env python3
"""DIAGNOSTIC: why the original prompt produced 115 UNCLEAR answers on the 500-sentence pilot.

INPUTS (all under data/processed/llm_review/, git-ignored)
    pilot500_input.parquet          500 distinct dev/test liver sentences, random (seed 20260922)
    pilot500_gemma4_v1/             answers with the original prompt (prompt read from its manifest)
    pilot500_gemma4_v2/             answers with the tightened prompt

WHAT IT MEASURES, COUNTS ONLY
    1. Structure: note type, section, length, digit and upper-case share, whether only the wide
       "hepat"/"liver*" prefix matched (no exact liver/hepatic/hepatis token).
    2. Wording: regex topic flags and one primary topic per sentence (fixed priority order).
    3. Model-assigned topic: gemma4:26b picks one letter from a fixed list (TOPIC_PROMPT). This is a
       model's reading, not ground truth; it is used only to describe what the UNCLEAR sentences are.
    4. Model dependence: qwen3.5:9b answers the ORIGINAL prompt on the same 500 sentences.

PRIVACY
    No sentence text or model reply is printed or written outside data/. Per-sentence results (keys,
    letters, answers) go to data/processed/llm_review/audit/; the aggregate tables go to
    diagnostics/llm_unclear_audit/unclear_audit_summary.csv.

USAGE
    scripts/run0919_env.sh diagnostics/llm_unclear_audit/unclear_audit.py
Requires the Ollama server with gemma4:26b and qwen3.5:9b. Nothing is installed or downloaded.
"""
import glob
import json
import os
import re
import sys
import time

import pandas as pd

sys.path.insert(0, ".")
from scripts.llm_sentence_review import ENDPOINT, post, text_key

OPTIONS = {"temperature": 0, "seed": 20260922, "num_predict": 16}   # as used for the v1/v2 pilots


def normalise(raw):
    """The v1/v2 one-word parser."""
    for w in "".join(c if c.isalpha() else " " for c in (raw or "").upper()).split():
        if w in ("YES", "NO", "UNCLEAR"):
            return w
    return "UNPARSED"
from scripts.note_phenotype import HEDGE, NEG_PRE, TARGET_ORGANS, _tokenize

D = "data/processed/llm_review"
AUDIT = f"{D}/audit"
SUMMARY = "diagnostics/llm_unclear_audit/unclear_audit_summary.csv"

TOPIC_PROMPT = (
    "You are reading a sentence from a hospital radiology report or clinical note that mentions the "
    "liver. What is the sentence mainly about? Answer with exactly one letter: "
    "A liver fat or steatosis; B liver size or shape; C a liver lesion, mass, cyst or nodule; "
    "D liver blood vessels or bile ducts; E liver blood tests or enzymes; "
    "F hepatitis, cirrhosis or another named liver disease; "
    "G the liver could not be fully seen or assessed; "
    "H a general statement that the liver is normal or unremarkable; "
    "I the word refers to something other than the liver, such as the hepatic flexure of the colon; "
    "J something else. Sentence: {sentence}")
TOPICS = {"A": "fat/steatosis", "B": "size/shape", "C": "lesion/mass/cyst", "D": "vessels/ducts",
          "E": "blood tests/enzymes", "F": "hepatitis/cirrhosis/other disease", "G": "not fully seen",
          "H": "normal/unremarkable", "I": "not the liver", "J": "something else"}

# Wording flags, then one primary topic per sentence by this priority order.
FLAGS = [
    ("fat term", r"steato|fatty|\bfat\b|nafld|nash|masld|mash|nafl|metabolic dysfunction"),
    ("echogenicity/attenuation", r"echogen|echotexture|attenuat"),
    ("not fully seen", r"not (?:well )?(?:seen|visuali[sz]ed|evaluated|assessed)|limited|suboptimal|obscur|incomplete|poorly"),
    ("lesion/mass/cyst", r"lesion|mass|cyst|hemangioma|nodul|metasta|tumou?r|\bhcc\b|hepatocellular|hypodens|hyperdens|hypoatten|enhanc"),
    ("cirrhosis/fibrosis", r"cirrho|fibros|portal hypertension|varic|ascites|elastograph|fibroscan|\bmeld\b"),
    ("hepatitis", r"hepatitis|\bhcv\b|\bhbv\b|hep ?[abc]\b"),
    ("blood tests/enzymes", r"\blfts?\b|liver function|liver enzyme|transaminase|\balt\b|\bast\b|alk ?phos|bilirubin|\bggt\b"),
    ("vessels/ducts", r"portal vein|hepatic vein|vasculature|doppler|duct|biliary|\bcbd\b|hepatopetal|hepatofugal|\bflow\b|artery"),
    ("size/shape", r"\bsize\b|enlarg|hepatomegaly|contour|\bspan\b|\bcm\b|measur|craniocaudal"),
    ("transplant/procedure", r"transplant|resection|hepatectomy|\btips\b|biopsy|embolization|ablation"),
    ("normal/unremarkable", r"unremarkable|\bnormal\b|within normal limits"),
]


def load_answers(folder):
    files = sorted(glob.glob(f"{D}/{folder}/shards/*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files]).drop_duplicates("key", keep="last")


def ask_letter(model, prompt, text, num_predict, letters):
    body = {"model": model, "prompt": prompt.format(sentence=text), "stream": False, "think": False,
            "keep_alive": "10m", "options": dict(OPTIONS, num_predict=num_predict)}
    reply = post(ENDPOINT, "/api/generate", body, 300).get("response") or ""
    m = re.search(r"\b([%s])\b" % letters, reply.upper())
    return m.group(1) if m else "?"


def unload(model):
    post(ENDPOINT, "/api/generate", {"model": model, "keep_alive": 0}, 120)


def features(p):
    low = p.text.str.lower()
    f = pd.DataFrame({"key": p.key, "note_type": p.note_type, "section": p.section})
    f["n_chars"] = p.text.str.len()
    f["length"] = pd.cut(f.n_chars, [0, 40, 80, 160, 100000], labels=["<=40", "41-80", "81-160", ">160"]).astype(str)
    f["digits>=10%"] = [sum(c.isdigit() for c in t) / max(len(t), 1) >= 0.10 for t in p.text]
    f["upper>=50%"] = [sum(c.isupper() for c in t) / max(sum(c.isalpha() for c in t), 1) >= 0.5 for t in p.text]
    f["prefix-only match"] = [not any(w in TARGET_ORGANS for w, _ in _tokenize(t)) for t in low]
    f["hedge phrase"] = [any(h in t for h in HEDGE) for t in low]
    f["negation phrase"] = [any(n in t for n in NEG_PRE) or bool(re.search(r"\bno\b|\bnot\b|without", t)) for t in low]
    for name, rx in FLAGS:
        f["flag: " + name] = low.str.contains(rx, regex=True)
    prim = []
    for i in range(len(f)):
        hit = [name for name, _ in FLAGS if f.iloc[i]["flag: " + name]]
        prim.append(hit[0] if hit else "none of these")
    f["primary wording topic"] = prim
    return f


def table(df, row, col, label, rows_out):
    t = pd.crosstab(df[row], df[col], margins=True, margins_name="All")
    if "UNCLEAR" in t.columns:
        t["UNCLEAR %"] = (100 * t["UNCLEAR"] / t["All"]).round(1)
    print(f"\n{label}\n{t.to_string()}")
    for r, vals in t.iterrows():
        for c, v in vals.items():
            rows_out.append({"table": label, "row": str(r), "column": str(c), "value": v})


def main():
    os.makedirs(AUDIT, exist_ok=True)
    p = pd.read_parquet(f"{D}/pilot500_input.parquet")
    p["key"] = [text_key(t) for t in p.text]
    old_prompt = json.load(open(f"{D}/pilot500_gemma4_v1/manifest.json"))["prompt"]
    f = features(p)
    f = f.merge(load_answers("pilot500_gemma4_v1")[["key", "answer"]].rename(columns={"answer": "v1 gemma old prompt"}), on="key")
    f = f.merge(load_answers("pilot500_gemma4_v2")[["key", "answer"]].rename(columns={"answer": "v2 gemma new prompt"}), on="key")

    cache = f"{AUDIT}/model_topics_and_qwen.parquet"
    if os.path.exists(cache):
        extra = pd.read_parquet(cache)
    else:
        t0 = time.time()
        topic = [ask_letter("gemma4:26b", TOPIC_PROMPT, t, 4, "A-J") for t in p.text]
        unload("gemma4:26b")
        print(f"topic letters done ({time.time() - t0:.0f}s)", flush=True)
        qwen = []
        for t in p.text:
            body = {"model": "qwen3.5:9b", "prompt": old_prompt.format(sentence=t), "stream": False,
                    "think": False, "keep_alive": "10m", "options": OPTIONS}
            qwen.append(normalise(post(ENDPOINT, "/api/generate", body, 300).get("response")))
        unload("qwen3.5:9b")
        print(f"qwen answers done ({time.time() - t0:.0f}s)", flush=True)
        extra = pd.DataFrame({"key": p.key, "topic_letter": topic, "qwen old prompt": qwen})
        extra.to_parquet(cache, index=False)
    f = f.merge(extra, on="key")
    f["model-assigned topic"] = f.topic_letter.map(TOPICS).fillna("unparsed")

    out = []
    v1, v2 = "v1 gemma old prompt", "v2 gemma new prompt"
    for row, label in [("model-assigned topic", "model-assigned topic x old-prompt answer"),
                       ("primary wording topic", "primary wording topic x old-prompt answer"),
                       ("note_type", "note type x old-prompt answer"),
                       ("section", "section x old-prompt answer"),
                       ("length", "sentence length (characters) x old-prompt answer"),
                       ("prefix-only match", "matched only by hepat*/liver* prefix x old-prompt answer"),
                       ("digits>=10%", "digits >= 10% of characters (lab-style lines) x old-prompt answer"),
                       ("upper>=50%", "mostly upper case x old-prompt answer"),
                       ("negation phrase", "negation word present x old-prompt answer"),
                       ("hedge phrase", "frozen-rule hedge phrase present x old-prompt answer")]:
        table(f, row, v1, label, out)
    table(f, "model-assigned topic", v2, "model-assigned topic x NEW-prompt answer", out)
    table(f, v1, "qwen old prompt", "gemma (rows) vs qwen (columns), both on the OLD prompt", out)
    table(f, v1, v2, "gemma old prompt (rows) vs new prompt (columns)", out)
    unc = f[f[v1] == "UNCLEAR"]
    flags = [c for c in f.columns if c.startswith("flag: ")]
    print(f"\nwording flags among the {len(unc)} old-prompt UNCLEAR sentences (a sentence can carry several):")
    for c in flags:
        n = int(unc[c].sum())
        print(f"  {c[6:]:<28} {n:>4}   (vs {int(f[f[v1] == 'NO'][c].sum())} of the {int((f[v1] == 'NO').sum())} NO sentences)")
        out.append({"table": "wording flags among old-prompt UNCLEAR", "row": c[6:], "column": "UNCLEAR", "value": n})
    pd.DataFrame(out).to_csv(SUMMARY, index=False)
    print(f"\nwrote {SUMMARY}")


if __name__ == "__main__":
    main()
