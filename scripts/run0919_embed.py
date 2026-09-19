#!/usr/bin/env python3
"""run_2026-09-19 Phase 3.4–3.5 — chunked Bio_ClinicalBERT embeddings, resumable shards, float16.
Admission vector = concat(mean over chunks, max over chunks) of attention-masked mean-pooled chunk vectors (1,536 dims).
Chunks of 512 tokens, stride 64, at most MAX_CHUNKS per admission. Logs counts and timings only.
  --pilot            encode pilot.parquet variant S, report tokens/s and projections
  --variant S|U|M    encode subsample.parquet variant, shards of SHARD admissions under data/processed/notes_embeddings_v1/<variant>/
"""
import argparse, os, sys, time, json, glob
import numpy as np, pandas as pd, torch
sys.path.insert(0, os.getcwd())
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
from transformers import AutoTokenizer, AutoModel
MODEL = "emilyalsentzer/Bio_ClinicalBERT"; MAX_LEN = 512; STRIDE = 64; MAX_CHUNKS = 12; BATCH = 32; SHARD = 1000
TEXTDIR = "data/processed/run_2026-09-19_notes_text"; EMBDIR = "data/processed/notes_embeddings_v1"

def device():
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")

def chunk_ids(tok, text):
    ids = tok(text, add_special_tokens=False, return_attention_mask=False)["input_ids"]
    body = MAX_LEN - 2; step = body - STRIDE; chunks = []
    for s in range(0, max(len(ids), 1), step):
        piece = ids[s:s + body]
        if not piece: break
        chunks.append([tok.cls_token_id] + piece + [tok.sep_token_id])
        if len(chunks) >= MAX_CHUNKS or s + body >= len(ids): break
    return chunks, len(ids)

@torch.no_grad()
def encode(model, tok, texts, dev):
    """texts: list[str] -> (n, 1536) float16, tokens processed."""
    all_chunks = []; owner = []; ntok = 0
    for i, t in enumerate(texts):
        ch, n = chunk_ids(tok, t or ""); ntok += sum(len(c) for c in ch)
        if not ch: ch = [[tok.cls_token_id, tok.sep_token_id]]
        all_chunks += ch; owner += [i] * len(ch)
    vecs = []
    for b in range(0, len(all_chunks), BATCH):
        batch = all_chunks[b:b + BATCH]; L = max(len(c) for c in batch)
        ids = torch.full((len(batch), L), tok.pad_token_id, dtype=torch.long); am = torch.zeros((len(batch), L), dtype=torch.long)
        for j, c in enumerate(batch): ids[j, :len(c)] = torch.tensor(c); am[j, :len(c)] = 1
        out = model(input_ids=ids.to(dev), attention_mask=am.to(dev)).last_hidden_state
        m = am.to(dev).unsqueeze(-1).float(); pooled = (out * m).sum(1) / m.sum(1).clamp(min=1)
        vecs.append(pooled.float().cpu().numpy())
    V = np.concatenate(vecs); owner = np.array(owner); res = np.zeros((len(texts), 2 * V.shape[1]), dtype=np.float32)
    for i in range(len(texts)):
        v = V[owner == i]; res[i, :V.shape[1]] = v.mean(0); res[i, V.shape[1]:] = v.max(0)
    return res.astype(np.float16), ntok

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--pilot", action="store_true"); ap.add_argument("--variant", default="S"); ap.add_argument("--budget_hours", type=float, default=5.0); ap.add_argument("--shards", default="", help="comma-separated shard ids to encode (default: all, in order)")
    a = ap.parse_args(); dev = device(); torch.set_num_threads(max(1, os.cpu_count() - 2))
    tok = AutoTokenizer.from_pretrained(MODEL); model = AutoModel.from_pretrained(MODEL).to(dev).eval()
    print(f"device {dev}; threads {torch.get_num_threads()}", flush=True)
    col = f"text_{a.variant}"
    if a.pilot:
        df = pd.read_parquet(f"{TEXTDIR}/pilot.parquet", columns=["hadm_id", col])
        t0 = time.time(); _, ntok = encode(model, tok, df[col].tolist(), dev); el = time.time() - t0
        tps = ntok / el; per_adm = el / len(df)
        proj = {n: round(n * per_adm / 3600, 2) for n in [8000, 12000, 20000, 30000, 60000]}
        cap = int(a.budget_hours * 3600 / per_adm)
        rep = {"device": str(dev), "n": int(len(df)), "tokens": int(ntok), "seconds": round(el, 1), "tokens_per_s": round(tps, 1),
               "seconds_per_admission": round(per_adm, 3), "projected_hours": proj, "max_admissions_in_budget": cap,
               "chosen_subsample": int(min(60000, max(8000, cap))) if cap >= 8000 else 0}
        os.makedirs("docs/run_2026-09-19/results", exist_ok=True)
        json.dump(rep, open("docs/run_2026-09-19/results/embed_pilot.json", "w"), indent=1); print(json.dumps(rep), flush=True); sys.exit()
    df = pd.read_parquet(f"{TEXTDIR}/subsample.parquet", columns=["hadm_id", col]).reset_index(drop=True)
    od = f"{EMBDIR}/{a.variant}"; os.makedirs(od, exist_ok=True)
    idx = df[["hadm_id"]].copy(); idx["shard"] = idx.index // SHARD; idx["row"] = idx.index % SHARD
    idx.to_parquet(f"{od}/index.parquet", index=False)
    t0 = time.time(); done = 0
    todo = [int(x) for x in a.shards.split(",")] if a.shards else range(int(idx.shard.max()) + 1)
    for sh in todo:
        f = f"{od}/shard_{sh:04d}.npy"
        if os.path.exists(f): continue
        part = df.iloc[sh * SHARD:(sh + 1) * SHARD]
        E, ntok = encode(model, tok, part[col].tolist(), dev)
        np.save(f + ".tmp.npy", E); os.replace(f + ".tmp.npy", f); done += len(part)
        print(f"[{a.variant}] shard {sh} ({len(part)} adm, {ntok:,} tok) — {done:,} done, {time.time()-t0:,.0f}s", flush=True)
    print(f"DONE variant {a.variant}", flush=True)
