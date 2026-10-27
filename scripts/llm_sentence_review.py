#!/usr/bin/env python3
"""Resumable local-LLM review of extracted liver sentences.

WHAT THIS IS
    Sends each distinct sentence from scripts/liver_sentences.py (--mode per_sentence --out) to a
    model served by Ollama on this machine, asks the fixed question of the chosen --variant, and stores
    a two-word answer: YES / NO / UNCLEAR, then CURRENT / PAST / FAMILY / NA. Built to run unattended
    for many hours: stop it at any point (Ctrl-C, crash, power loss) and rerun the same command, and it
    continues where it left off.

WHAT IT DOES NOT DECIDE
    How sentence answers become an admission label, which model is final, and whether PAST mentions or
    UNCLEAR answers count. Those are protocol decisions (docs/llm_review_protocol.md).

PROMPT HISTORY
    v1  the question in scripts/llm_timing_test.py.
    v2  two sentences added reserving UNCLEAR for uncertain statements about liver fat (pilot of 500
        dev+test sentences: UNCLEAR 115 -> 8).
    v3  the literature audit's changes: the note type and nearest heading are given; explicit rules for
        the errors published studies report (fat in other organs or around the liver, focal fat versus
        focal fatty sparing, "rule out" requests, NAFLD/NASH/MASLD/MASH, imaging signs, coarse
        echotexture, a fixed hedge list); a second word separating current, past and family mentions.
        Developed on the development partition only.
    v4  v3 plus one NO rule: alcohol-related liver disease, alcoholic hepatitis, cirrhosis and fibrosis
        count only when the sentence also says the liver is fatty. Added after the full v3 run, where
        such sentences were the main source of positives the frozen rule did not share.
    VARIANTS holds v3, v4, and the v3-based variants used for the prompt-sensitivity analysis: two
    paraphrases, a few-shot version, and a version that also shows the neighbouring sentences.

OUTPUT FORMAT AND PROBABILITIES
    Plain text, parsed strictly: a reply is `strict` when it is exactly one answer word and one timing
    word. JSON-schema output was tested and not used: on Ollama 0.34.2 with this model, log
    probabilities are returned for the first generated token only, and under a schema that token is
    the opening brace, so the class probability would be lost. With plain text the first token is the
    answer, and p_yes / p_no / p_unclear are read from its top alternatives. done_reason is stored.

DEDUPLICATION
    A unit is keyed by the SHA-256 of its text (case folded, whitespace collapsed) together with the
    context fields the variant shows the model (note type and heading; plus the neighbouring sentences
    for the context variant). Each key is asked once; --assemble maps answers back to every input row.

RESUME, CONSISTENCY AND VERSION PINNING
    The first run writes <out>/manifest.json: variant, prompt and its hash, model and digest, model
    details, Ollama version, options, hardware, and the input's SHA-256. A later run against the same
    <out> refuses if the model, digest, prompt, options, input or Ollama version differ, so one
    directory never mixes them. Cloud-served models (":cloud" or "-cloud") are refused. Answers go to
    <out>/shards/ in files of --shard rows, written to a temporary name and renamed.

FAILURES
    Each request is tried RETRIES times. An item that still fails is stored with a null answer and its
    error class, and is skipped on later runs unless --retry-errors. An unreachable server or a
    missing model stops the run instead, without recording anything for the unasked items.

GOLD_HOLDOUT
    Refuses input containing a GOLD_HOLDOUT admission (splits_v1) unless --include-gold. Answers on
    those admissions would have to be locked before adjudication, which is a protocol decision.

PRIVACY
    Never prints sentence text or model replies: progress is counts, rates and time remaining only.
    Replies, truncated to REPLY_CHARS, are stored in the shards for auditing, so --out must be under
    data/ (git-ignored) or outside the repository.

USAGE
    caffeinate -i scripts/run0919_env.sh scripts/llm_sentence_review.py \\
        --input <sentences.parquet> --out data/processed/llm_review/<run>
    ... --variant v3_context   one of VARIANTS (default v3)
    ... --limit 500            stop after 500 new distinct units (a pilot)
    ... --max-hours 8          stop cleanly after the first shard that ends past 8 hours
    ... --assemble             write <out>/sentence_answers.parquet: one row per input sentence, no text
caffeinate -i keeps the Mac awake while the run lasts. Keep one request at a time (--workers 1, server
OLLAMA_NUM_PARALLEL=1): answers were identical across reruns only under that setting.
Requires an Ollama server; nothing is installed or downloaded.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

sys.path.insert(0, ".")
from scripts.masld_config import SPLITS_V1

ENDPOINT = "http://localhost:11434"
MODEL = "gemma4:26b"        # 47/50 on the invented probe set, against 43/50 for qwen3.5:9b
SEED = 20260922
OPTIONS = {"temperature": 0, "seed": SEED, "num_predict": 12}
TOP_LOGPROBS = 10
KEEP_ALIVE = "30m"
TIMEOUT_S = 300
RETRIES = 3
REPLY_CHARS = 64
SHARD = 500
CONTEXT_CHARS = 300

ANSWERS = ("YES", "NO", "UNCLEAR")
TIMINGS = ("CURRENT", "PAST", "FAMILY", "NA")
NOTE_LABEL = {"discharge": "discharge summary", "radiology_inpatient": "radiology report",
              "radiology_outpatient": "radiology report"}

RULES = (
    "Answer with two words.\n"
    "First word:\n"
    "YES if the sentence states that the liver is fatty or steatotic. This includes steatosis, fatty liver, "
    "or fatty infiltration or fatty change of the liver; NAFLD, NAFL, NASH, MASLD, MASH, MAFLD or "
    "steatohepatitis; a diffusely echogenic or hyperechoic liver; decreased liver attenuation, or attenuation "
    "below the spleen or below 40 HU; liver signal loss on out-of-phase MRI; and focal fatty sparing, which "
    "means the rest of the liver is fatty. Wording such as 'consistent with' or 'compatible with' counts as YES.\n"
    "NO if the sentence says the liver is not fatty, or says nothing about fat in the liver. This includes fat "
    "only in another organ or tissue (pancreas, kidney, spleen, bone marrow, fat around the liver, falciform "
    "ligament), focal fat or a single fatty lesion, a request to evaluate for or rule out fatty liver, and "
    "liver tests or other liver findings that do not mention fat.\n"
    "UNCLEAR if the sentence suggests liver fat but is uncertain (likely, probable, suggestive of, possible, "
    "may represent, cannot exclude, borderline, questionable), or describes only coarse or heterogeneous "
    "liver echotexture.\n"
    "Second word:\n"
    "CURRENT if the finding is about this patient now; PAST if it refers to a prior study or the patient's "
    "history; FAMILY if it is about a relative; NA if the first word is NO.\n")

# Every template keeps the per-sentence fields (note type, heading, context, sentence) at the END, so
# the long fixed instructions form an identical prefix that Ollama's prompt cache reuses; with the
# note type first, the v3 pilot ran at about a quarter of the speed.
V3 = ("You are reviewing one sentence from a hospital record. "
      "Does the sentence state that this patient's liver is fatty (hepatic steatosis)?\n\n"
      + RULES +
      "\nReply with exactly two words, for example: YES CURRENT\n\n"
      "The sentence is from a {note_label}{heading_clause}.\n"
      "{context_block}Sentence: {sentence}")

# v4: v3 plus one NO rule. In the full v3 run, a third of the admissions the model alone called positive
# rested on sentences with no word about fat, mostly alcohol-related liver disease and cirrhosis.
ALCOHOL_RULE = ("Alcohol-related or alcoholic liver disease, alcoholic hepatitis, and cirrhosis or liver fibrosis "
                "are NO unless the sentence also says the liver is fatty or steatotic (alcoholic fatty liver or "
                "alcoholic steatohepatitis is YES).")
RULES_V4 = RULES.replace("liver tests or other liver findings that do not mention fat.\n",
                         "liver tests or other liver findings that do not mention fat. " + ALCOHOL_RULE + "\n")
assert RULES_V4 != RULES
V4 = V3.replace(RULES, RULES_V4)

PARAPHRASE_A = (
    "Decide whether the sentence below asserts hepatic steatosis (a fatty liver) for this patient.\n\n"
    "Reply YES when the sentence asserts it: steatosis, fatty liver, fatty infiltration or change of the liver, "
    "NAFLD, NAFL, NASH, MASLD, MASH, MAFLD, steatohepatitis, a diffusely echogenic or hyperechoic liver, low liver "
    "attenuation (below the spleen or under 40 HU), out-of-phase signal loss, or focal fatty sparing. "
    "'Consistent with' and 'compatible with' are assertions.\n"
    "Reply NO when the sentence denies a fatty liver or does not address fat in the liver at all, including fat "
    "in other organs or around the liver, falciform ligament fat, focal fat or a fatty lesion, requests to rule out "
    "fatty liver, and liver findings unrelated to fat.\n"
    "Reply UNCLEAR when liver fat is raised with uncertainty (likely, probable, suggestive of, possible, may "
    "represent, cannot exclude, borderline, questionable) or only coarse or heterogeneous echotexture is described.\n"
    "Then add CURRENT (this patient now), PAST (prior study or history), FAMILY (a relative), or NA (after NO).\n\n"
    "Output two words only, such as: NO NA\n\n"
    "It is taken from a {note_label}{heading_clause}.\n"
    "{context_block}Sentence: {sentence}")

PARAPHRASE_B = (
    "Task: label one sentence from a hospital record.\n"
    "Label 1 - is this patient's liver said to be fatty?\n"
    "  YES: steatosis/fatty liver/fatty infiltration of the liver; NAFLD, NAFL, NASH, MASLD, MASH, MAFLD, "
    "steatohepatitis; diffusely echogenic or hyperechoic liver; low liver attenuation (< spleen or < 40 HU); "
    "out-of-phase signal loss; focal fatty sparing; 'consistent with'/'compatible with'.\n"
    "  NO: liver not fatty, or no statement about liver fat; fat in other organs, around the liver or in the "
    "falciform ligament; focal fat or a fatty lesion; 'rule out' or 'evaluate for' requests; other liver findings.\n"
    "  UNCLEAR: liver fat with hedging (likely, probable, suggestive of, possible, may represent, cannot "
    "exclude, borderline, questionable); coarse or heterogeneous echotexture only.\n"
    "Label 2 - CURRENT (this patient now), PAST (prior study or history) or FAMILY (a relative); "
    "use NA only when label 1 is NO.\n"
    "Reply with label 1 then label 2, two words, for example: NO NA or YES CURRENT\n\n"
    "Source: {note_label}{heading_clause}.\n"
    "{context_block}Sentence: {sentence}")

FEW_SHOT = ("Examples (invented sentences):\n"
            "Sentence: The liver is diffusely echogenic, compatible with steatosis. -> YES CURRENT\n"
            "Sentence: History of NASH diagnosed on biopsy in 2015. -> YES PAST\n"
            "Sentence: Diffuse fatty infiltration with focal sparing adjacent to the gallbladder. -> YES CURRENT\n"
            "Sentence: Fatty atrophy of the pancreas; the liver is unremarkable. -> NO NA\n"
            "Sentence: Ultrasound requested to evaluate for fatty liver. -> NO NA\n"
            "Sentence: Mildly increased hepatic echogenicity may represent steatosis. -> UNCLEAR CURRENT\n"
            "Sentence: Her mother has fatty liver disease. -> YES FAMILY\n\n")

CONTEXT_BLOCK = ("The sentences just before and after it are shown for context only; label only the target sentence.\n"
                 "Before: {prev_text}\nAfter: {next_text}\n")

# name -> (template, context fields in the key, few-shot block, show neighbours)
VARIANTS = {
    "v3": (V3, ("note_type", "heading"), "", False),
    "v3_paraphrase_a": (PARAPHRASE_A, ("note_type", "heading"), "", False),
    "v3_paraphrase_b": (PARAPHRASE_B, ("note_type", "heading"), "", False),
    "v3_fewshot": (V3, ("note_type", "heading"), FEW_SHOT, False),
    "v3_context": (V3, ("note_type", "heading", "prev_text", "next_text"), "", True),
    "v4": (V4, ("note_type", "heading"), "", False),
}

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SHARD_RE = re.compile(r"answers_(\d{5})\.parquet$")
CHECKED = ("variant", "model", "model_digest", "prompt_sha256", "options", "input_sha256", "ollama_version")


class ServerDown(Exception):
    """The server is unreachable or lacks the model: stop instead of recording failures."""


# ----------------------------------------------------------------------------- prompts and parsing
def norm(s):
    return " ".join((s or "").lower().split())


def text_key(text):
    return hashlib.sha256(norm(text).encode()).hexdigest()


def unit_key(row, fields):
    parts = [norm(row.get("text"))] + [f"{f}={norm(row.get(f))}" for f in fields]
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def build_prompt(variant, row):
    template, _, few_shot, show_context = VARIANTS[variant]
    heading = (row.get("heading") or "").strip()
    ctx = CONTEXT_BLOCK.format(prev_text=(row.get("prev_text") or "")[-CONTEXT_CHARS:] or "(none)",
                               next_text=(row.get("next_text") or "")[:CONTEXT_CHARS] or "(none)") if show_context else ""
    return few_shot + template.format(
        note_label=NOTE_LABEL.get(row.get("note_type") or "", "clinical note or radiology report"),
        heading_clause=f' under the heading "{heading}"' if heading else "",
        context_block=ctx, sentence=(row.get("text") or "").strip())


def parse_reply(raw):
    """-> (answer, timing, strict). answer/timing are UNPARSED when absent; strict = exactly two valid words."""
    words = "".join(c if c.isalpha() else " " for c in (raw or "").upper()).split()
    answer = next((w for w in words if w in ANSWERS), "UNPARSED")
    timing = next((w for w in words if w in TIMINGS), "UNPARSED")
    strict = len(words) == 2 and words[0] in ANSWERS and words[1] in TIMINGS
    return answer, timing, strict


def class_probs(logprobs):
    """P(YES), P(NO), P(UNCLEAR) from the first generated token's top alternatives (None if absent)."""
    if not logprobs:
        return None, None, None
    p = dict.fromkeys(ANSWERS, 0.0)
    for alt in logprobs[0].get("top_logprobs") or []:
        tok = "".join(c for c in (alt.get("token") or "").upper() if c.isalpha())
        hits = [a for a in ANSWERS if tok and a.startswith(tok)]
        if len(hits) == 1:
            p[hits[0]] += math.exp(alt.get("logprob", -math.inf))
    return p["YES"], p["NO"], p["UNCLEAR"]


# ----------------------------------------------------------------------------- server
def post(endpoint, path, payload, timeout):
    req = urllib.request.Request(
        endpoint + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get(endpoint, path, timeout=15):
    with urllib.request.urlopen(endpoint + path, timeout=timeout) as r:
        return json.load(r)


def server_facts(endpoint, model):
    """-> (digest, ollama version, model details). Refuses cloud models; ServerDown if unavailable."""
    if ":cloud" in model or model.endswith("-cloud"):
        sys.exit(f"REFUSING: {model} is served from Ollama's cloud; MIMIC text must stay on this machine")
    try:
        tags = get(endpoint, "/api/tags").get("models", [])
        version = get(endpoint, "/api/version").get("version")
    except urllib.error.URLError as e:
        raise ServerDown(f"no Ollama server at {endpoint} ({type(e.reason).__name__})")
    m = next((m for m in tags if m["name"] == model), None)
    if m is None:
        raise ServerDown(f"model {model} is not on the server; pull it first")
    show = post(endpoint, "/api/show", {"model": model}, 60)
    details = dict(show.get("details") or {}, parameters=show.get("parameters"),
                   remote_host=m.get("remote_host"))
    if details.get("remote_host"):
        sys.exit(f"REFUSING: {model} is a remote model; MIMIC text must stay on this machine")
    return m["digest"], version, details


def hardware():
    def sysctl(k):
        try:
            return subprocess.run(["sysctl", "-n", k], capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
    return {"machine": platform.machine(), "system": f"{platform.system()} {platform.release()}",
            "cpu": sysctl("machdep.cpu.brand_string"), "memory_bytes": sysctl("hw.memsize")}


def ask(endpoint, model, prompt):
    body = {"model": model, "prompt": prompt, "stream": False, "think": False, "keep_alive": KEEP_ALIVE,
            "logprobs": True, "top_logprobs": TOP_LOGPROBS, "options": OPTIONS}
    err = None
    for attempt in range(RETRIES):
        t0 = time.perf_counter()
        try:
            r = post(endpoint, "/api/generate", body, TIMEOUT_S)
            reply = r.get("response") or ""
            answer, timing, strict = parse_reply(reply)
            p_yes, p_no, p_unclear = class_probs(r.get("logprobs"))
            return {"answer": answer, "timing": timing, "strict": strict, "p_yes": p_yes, "p_no": p_no,
                    "p_unclear": p_unclear, "reply": reply[:REPLY_CHARS], "done_reason": r.get("done_reason"),
                    "error": None, "seconds": time.perf_counter() - t0}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ServerDown(f"model {model} not found on the server")
            err = f"HTTPError {e.code}"
        except urllib.error.URLError as e:
            if isinstance(e.reason, ConnectionRefusedError):
                raise ServerDown(f"connection to {endpoint} refused")
            err = f"URLError {type(e.reason).__name__}"
        except (TimeoutError, ConnectionError) as e:
            err = type(e).__name__
        if attempt < RETRIES - 1:
            time.sleep(2 ** (attempt + 1))
    return {"answer": None, "timing": None, "strict": None, "p_yes": None, "p_no": None, "p_unclear": None,
            "reply": None, "done_reason": None, "error": err, "seconds": None}


# ----------------------------------------------------------------------------- input and output
def check_out(out):
    path = os.path.realpath(out)
    if path.startswith(REPO + os.sep) and not path.startswith(os.path.join(REPO, "data") + os.sep):
        sys.exit(f"REFUSING: --out {out} is inside the repository but not under data/; "
                 "the shards hold model replies and must stay git-ignored")


def load_input(path, variant):
    df = pd.read_parquet(path)
    missing = {"hadm_id", "sid", "text"} - set(df.columns)
    if missing:
        sys.exit(f"REFUSING: {path} lacks {', '.join(sorted(missing))}; "
                 "expected scripts/liver_sentences.py --mode per_sentence output")
    fields = VARIANTS[variant][1]
    for f in fields:
        if f not in df.columns:
            df[f] = ""
    df["key"] = [unit_key(r, fields) for r in df[["text", *fields]].to_dict("records")]
    return df


def check_gold(df, include_gold):
    sp = pd.read_parquet(os.path.join(REPO, SPLITS_V1), columns=["hadm_id", "partition"])
    gold = set(sp.hadm_id[sp.partition == "GOLD_HOLDOUT"].astype("int64"))
    n = int(df.hadm_id.astype("int64").isin(gold).sum())
    if n and not include_gold:
        sys.exit(f"REFUSING: input has {n:,} sentence row(s) from GOLD_HOLDOUT admissions. Answers on "
                 "them must be locked before adjudication; pass --include-gold only once that is decided.")
    return n


def open_manifest(out, current):
    path = os.path.join(out, "manifest.json")
    if os.path.exists(path):
        with open(path) as f:
            old = json.load(f)
        diff = [k for k in CHECKED if old.get(k) != current[k]]
        if diff:
            sys.exit(f"REFUSING: {out} was started with a different {', '.join(diff)}; "
                     "use a new --out directory")
        return old
    with open(path + ".tmp", "w") as f:
        json.dump(current, f, indent=1)
    os.replace(path + ".tmp", path)
    return current


def load_answers(out):
    """-> (latest row per key, next shard number)."""
    files = sorted(glob.glob(os.path.join(out, "shards", "answers_*.parquet")))
    if not files:
        return pd.DataFrame(columns=["key", "answer", "timing", "strict", "p_yes", "p_no", "p_unclear",
                                     "reply", "done_reason", "error", "seconds"]), 0
    latest = pd.concat([pd.read_parquet(f) for f in files]).drop_duplicates("key", keep="last")
    return latest, int(SHARD_RE.search(files[-1]).group(1)) + 1


def write_parquet(df, path):
    df.to_parquet(path + ".tmp", index=False)
    os.replace(path + ".tmp", path)


def hours(s):
    return f"{s / 3600:.1f} h" if s >= 3600 else f"{s / 60:.0f} min"


# ----------------------------------------------------------------------------- run and assemble
def run(a, df, units):
    digest, version, details = server_facts(a.endpoint, a.model)
    template, _, few, show = VARIANTS[a.variant]
    prompt_spec = few + template + (CONTEXT_BLOCK if show else "")
    current = {"script": "scripts/llm_sentence_review.py", "variant": a.variant, "prompt": prompt_spec,
               "prompt_sha256": hashlib.sha256(prompt_spec.encode()).hexdigest(),
               "key_fields": list(VARIANTS[a.variant][1]), "model": a.model, "model_digest": digest,
               "model_details": details, "ollama_version": version, "options": OPTIONS,
               "think": False, "logprobs": True, "top_logprobs": TOP_LOGPROBS, "keep_alive": KEEP_ALIVE,
               "workers": a.workers, "endpoint": a.endpoint, "hardware": hardware(),
               "input_path": a.input, "input_sha256": sha256_file(a.input), "input_rows": len(df),
               "distinct_units": len(units),
               "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    open_manifest(a.out, current)
    latest, nxt = load_answers(a.out)
    ok = set(latest.key[latest.error.isna()])
    failed = set(latest.key[latest.error.notna()])
    skip = ok if a.retry_errors else ok | failed
    todo = units[~units.key.isin(skip)]
    if a.limit:
        todo = todo.head(a.limit)
    print(f"variant {a.variant} | model {a.model} ({digest[:12]}) | ollama {version} | input rows {len(df):,} | "
          f"distinct units {len(units):,} | answered {len(ok):,} | failed {len(failed):,} | asking now {len(todo):,}",
          flush=True)
    if todo.empty:
        return

    ex = ThreadPoolExecutor(a.workers)
    t0 = time.time()
    asked = 0
    tally = {}
    loose = 0
    try:
        for start in range(0, len(todo), a.shard):
            chunk = todo.iloc[start:start + a.shard]
            futs = [ex.submit(ask, a.endpoint, a.model, build_prompt(a.variant, r))
                    for r in chunk.to_dict("records")]
            buf = []
            try:
                for key, f in zip(chunk.key, futs):
                    buf.append(dict(key=key, **f.result()))
            finally:      # keep finished answers when interrupted or the server goes away
                if buf:
                    write_parquet(pd.DataFrame(buf), os.path.join(a.out, "shards", f"answers_{nxt:05d}.parquet"))
                    nxt += 1
                    asked += len(buf)
                    for r in buf:
                        k = r["answer"] or "ERROR"
                        tally[k] = tally.get(k, 0) + 1
                        loose += r["strict"] is False
            el = time.time() - t0
            print(f"[{el:7.0f}s] {asked:,}/{len(todo):,} this run | {asked / el:.2f}/s | "
                  f"remaining {hours((len(todo) - asked) * el / asked)} | not two-word {loose} | "
                  f"unparsed {tally.get('UNPARSED', 0)} | errors {tally.get('ERROR', 0)}", flush=True)
            if a.max_hours and el > a.max_hours * 3600 and asked < len(todo):
                print(f"stopping: --max-hours {a.max_hours} reached; rerun to continue", flush=True)
                break
    except ServerDown as e:
        ex.shutdown(wait=False, cancel_futures=True)
        sys.exit(f"STOPPED: {e}. {asked:,} answers saved; rerun the same command to continue.")
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        print(f"\ninterrupted: {asked:,} answers saved; rerun the same command to continue", flush=True)
        sys.exit(130)
    ex.shutdown()
    print("this run: " + " | ".join(f"{k} {v:,}" for k, v in sorted(tally.items())), flush=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def assemble(a, df):
    path = os.path.join(a.out, "manifest.json")
    if not os.path.exists(path):
        sys.exit(f"nothing to assemble: {path} not found")
    with open(path) as f:
        man = json.load(f)
    if man["input_sha256"] != sha256_file(a.input) or man.get("variant", "v3") != a.variant:
        sys.exit(f"REFUSING: {a.input} with --variant {a.variant} is not what {a.out} was run on")
    latest, _ = load_answers(a.out)
    cols = [c for c in ("hadm_id", "sid", "note_type", "section", "reason", "char_start", "char_end", "key")
            if c in df.columns]
    keep = [c for c in ("key", "answer", "timing", "strict", "p_yes", "p_no", "p_unclear", "error") if c in latest.columns]
    m = df[cols].merge(latest[keep], on="key", how="left")
    out = os.path.join(a.out, "sentence_answers.parquet")
    write_parquet(m, out)
    status = m.answer.fillna(m.error.map(lambda e: "ERROR" if isinstance(e, str) else "NOT ASKED"))
    print(f"wrote {out} ({len(m):,} rows, {m.hadm_id.nunique():,} admissions)")
    print("  " + " | ".join(f"{k} {v:,}" for k, v in status.value_counts().sort_index().items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--input", required=True, help="liver_sentences.py --mode per_sentence parquet")
    ap.add_argument("--out", required=True, help="output directory (under data/ or outside the repo)")
    ap.add_argument("--variant", choices=sorted(VARIANTS), default="v3")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--endpoint", default=ENDPOINT)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--shard", type=int, default=SHARD, help="answers per saved file")
    ap.add_argument("--limit", type=int, default=0, help="ask at most this many new distinct units")
    ap.add_argument("--max-hours", type=float, default=0)
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--include-gold", action="store_true")
    ap.add_argument("--assemble", action="store_true")
    a = ap.parse_args()

    check_out(a.out)
    df = load_input(a.input, a.variant)
    n_gold = check_gold(df, a.include_gold)
    if n_gold:
        print(f"--include-gold: {n_gold:,} GOLD_HOLDOUT sentence rows are in scope", flush=True)
    if a.assemble:
        return assemble(a, df)
    os.makedirs(os.path.join(a.out, "shards"), exist_ok=True)
    units = df.drop_duplicates("key")
    try:
        run(a, df, units)
    except ServerDown as e:
        sys.exit(f"STOPPED: {e}")


if __name__ == "__main__":
    main()
