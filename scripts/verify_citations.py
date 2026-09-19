#!/usr/bin/env python3
"""run_2026-09-19 Phase 10.4 — verify the citation registry against PubMed and Crossref.

Reads docs/references/registry.yaml. For each entry, tries in order:
  PubMed by PMID -> PubMed by DOI -> PubMed by exact title -> PubMed by author+year(+journal/keywords)
  -> Crossref by DOI -> Crossref by title (query.bibliographic, rows=5) -> Crossref by author+year.
A match is accepted ONLY when
  * an identifier (PMID/DOI) given in the registry resolves directly to a record, and, when the
    registry also gives a DOI, the record's DOI agrees; or
  * the returned title equals the registry title after normalisation (lowercase, strip
    punctuation and whitespace); or
  * the registry has no title and no identifier, exactly ONE candidate is returned for the
    author + year (+ journal / keywords) query, and its first-author surname, year and (if the
    registry gives one) journal all match. These are labelled as lower-confidence.
Every bibliographic field written out comes from the API response, never from this script.
Raw responses are saved under data/processed/run_2026-09-19_scratch/citations/ (no patient data).
Rate limit: >= 0.34 s between requests. Only citation strings leave the machine.

Run: scripts/run0919_env.sh scripts/verify_citations.py
"""
import json, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "docs/references/registry.yaml"
OUT_VERIFIED = ROOT / "docs/references/verified_references.md"
OUT_UNRESOLVED = ROOT / "docs/references/unresolved.md"
OUT_JSON = ROOT / "docs/run_2026-09-19/results/citations.json"
RAW_DIR = ROOT / "data/processed/run_2026-09-19_scratch/citations"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
CROSSREF = "https://api.crossref.org/works"
UA = "masld_mimic-citation-verifier/0.1 (academic citation verification; Python urllib)"
SLEEP = 0.34
_last = [0.0]
_cands = []   # per-entry: candidate records seen but NOT accepted (listed for human review)
# PubMed stopwords are not indexed; a word[ti] clause for one of them returns "phrase not found" and 0 results.
PUBMED_STOPWORDS = set("""a about again all almost also although always among an and another any are as at be because been
before being between both but by can could did do does done due during each either enough especially etc for found from
further had has have having here how however i if in into is it its itself just kg km made mainly make may mg might ml mm
most mostly must nearly neither no nor obtained of often on our overall perhaps pmid quite rather really regarding seem seen
several should show showed shown shows significantly since so some such than that the their theirs them then there
therefore these they this those through thus to upon use used using various very was we were what when which while with
within without would""".split())
ERRATA = ' NOT "published erratum"[pt] NOT "retraction of publication"[pt]'


def note_cands(source, recs, limit=5):
    for r in recs[:limit]:
        fa = r["authors"][0] if r["authors"] else "?"
        _cands.append(f"{source} | {fa} | {r.get('year')} | {r.get('journal') or r.get('journal_abbrev') or '?'} | '{r['title']}' | DOI {r.get('doi') or '—'} | PMID {r.get('pmid') or '—'}")


# ----------------------------------------------------------------------------- http
def _get(url, label, binary=False):
    """GET with rate limiting and one retry after 30 s. Saves the raw body under RAW_DIR."""
    wait = SLEEP - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    body, err = None, None
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
            break
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code == 404:
                break
        except Exception as e:  # network
            err = type(e).__name__
        if attempt == 1:
            time.sleep(30)
    _last[0] = time.time()
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", label)[:120]
    if body is not None:
        (RAW_DIR / safe).write_bytes(body)
    return body, err


def pubmed(endpoint, label, **params):
    params.setdefault("db", "pubmed")
    url = EUTILS + endpoint + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return _get(url, label)


def crossref(label, path="", **params):
    url = CROSSREF + path + ("?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote) if params else "")
    body, err = _get(url, label)
    if body is None:
        return None, err
    try:
        return json.loads(body), None
    except ValueError:
        return None, "non-JSON response"


# ----------------------------------------------------------------------------- helpers
def norm_title(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def norm_name(s):
    return re.sub(r"[^a-z]+", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())


def norm_journal(s):
    return re.sub(r"[^a-z]+", "", (s or "").lower())


def journal_match(reg_j, rec):
    """Registry journal vs record: compare against the record's ISO abbreviation, MedlineTA and full title."""
    if not reg_j:
        return True
    cands = [rec.get("journal_abbrev"), rec.get("journal_medline"), rec.get("journal"), *rec.get("journal_short_list", [])]
    rj = norm_journal(reg_j)
    return any(rj == norm_journal(c) or (c and rj and (rj in norm_journal(c) or norm_journal(c) in rj)) for c in cands if c)


def strip_trailing_period(s):
    return re.sub(r"\.\s*$", "", s or "")


# ----------------------------------------------------------------------------- pubmed parsing
def parse_pubmed_xml(xml_bytes):
    """Return a list of records (dict) from an efetch PubmedArticleSet. Fields only from the XML."""
    recs = []
    root = ET.fromstring(xml_bytes)
    for art in root.iter("PubmedArticle"):
        mc = art.find("MedlineCitation")
        a = mc.find("Article")
        j = a.find("Journal")
        ji = j.find("JournalIssue") if j is not None else None
        rec = {"source_db": "PubMed",
               "pmid": (mc.findtext("PMID") or "").strip(),
               "title": strip_trailing_period("".join(a.find("ArticleTitle").itertext()) if a.find("ArticleTitle") is not None else ""),
               "journal": j.findtext("Title") if j is not None else None,
               "journal_abbrev": j.findtext("ISOAbbreviation") if j is not None else None,
               "journal_medline": mc.findtext("MedlineJournalInfo/MedlineTA"),
               "volume": ji.findtext("Volume") if ji is not None else None,
               "issue": ji.findtext("Issue") if ji is not None else None,
               "year": None, "pages": a.findtext("Pagination/MedlinePgn"), "doi": None, "authors": []}
        if ji is not None:
            rec["year"] = ji.findtext("PubDate/Year") or (ji.findtext("PubDate/MedlineDate") or "")[:4]
        if not rec["year"]:
            rec["year"] = a.findtext("ArticleDate/Year")
        for el in a.findall("ELocationID"):
            if el.get("EIdType") == "doi" and (el.text or "").strip():
                rec["doi"] = el.text.strip()
        if not rec["doi"]:
            for aid in art.findall("PubmedData/ArticleIdList/ArticleId"):
                if aid.get("IdType") == "doi" and (aid.text or "").strip():
                    rec["doi"] = aid.text.strip()
        for au in a.findall("AuthorList/Author"):
            ln, ini, coll = au.findtext("LastName"), au.findtext("Initials"), au.findtext("CollectiveName")
            if ln:
                rec["authors"].append(f"{ln} {ini or ''}".strip())
            elif coll:
                rec["authors"].append(coll)
        recs.append(rec)
    return recs


def pubmed_search(term, label, retmax=20):
    body, err = pubmed("esearch.fcgi", label, term=term, retmode="json", retmax=retmax)
    if body is None:
        return None, err
    try:
        d = json.loads(body)["esearchresult"]
    except (ValueError, KeyError):
        return None, "non-JSON esearch response"
    return {"count": int(d.get("count", 0)), "ids": d.get("idlist", []), "translation": d.get("querytranslation")}, None


def pubmed_fetch(pmids, label):
    if not pmids:
        return [], None
    body, err = pubmed("efetch.fcgi", label, id=",".join(pmids), retmode="xml")
    if body is None:
        return None, err
    try:
        return parse_pubmed_xml(body), None
    except ET.ParseError:
        return None, "XML parse error"


# ----------------------------------------------------------------------------- crossref parsing
def parse_crossref_item(it):
    date = it.get("issued", {}).get("date-parts", [[None]])[0]
    return {"source_db": "Crossref",
            "doi": it.get("DOI"),
            "title": strip_trailing_period((it.get("title") or [""])[0]),
            "journal": (it.get("container-title") or [None])[0],
            "journal_short_list": it.get("short-container-title") or [],
            "journal_abbrev": (it.get("short-container-title") or [None])[0],
            "volume": it.get("volume"), "issue": it.get("issue"), "pages": it.get("page"),
            "year": str(date[0]) if date and date[0] else None,
            "type": it.get("type"), "publisher": it.get("publisher"), "event": (it.get("event") or {}).get("name"),
            "authors": [f"{a.get('family','')} {a.get('given','')}".strip() for a in it.get("author", [])],
            "pmid": None}


# ----------------------------------------------------------------------------- strategies
def first_author_ok(entry, rec):
    if not entry.get("first_author") or not rec["authors"]:
        return False
    return norm_name(rec["authors"][0].split(" ")[0]) == norm_name(entry["first_author"]) or \
        norm_name(rec["authors"][0]).startswith(norm_name(entry["first_author"]))


def year_ok(entry, rec):
    return entry.get("year") is None or str(entry["year"]) == str(rec.get("year") or "")[:4]


def doi_ok(entry, rec):
    return not entry.get("doi") or not rec.get("doi") or entry["doi"].lower() == rec["doi"].lower()


def try_pubmed_pmid(entry, log):
    pmid = entry.get("pmid")
    if not pmid:
        return None
    recs, err = pubmed_fetch([str(pmid)], f"{entry['id']}_pubmed_pmid.xml")
    if err:
        log.append(f"efetch by PMID {pmid}: {err}"); return None
    if len(recs) != 1 or recs[0]["pmid"] != str(pmid):
        log.append(f"efetch by PMID {pmid}: returned {len(recs)} record(s), none with that PMID"); return None
    rec = recs[0]
    if not doi_ok(entry, rec):
        log.append(f"efetch by PMID {pmid}: record DOI {rec['doi']} differs from registry DOI {entry['doi']}"); return None
    if entry.get("title") and norm_title(entry["title"]) != norm_title(rec["title"]):
        log.append(f"efetch by PMID {pmid}: record title differs from registry title"); return None
    if not first_author_ok(entry, rec):
        log.append(f"efetch by PMID {pmid}: first author {rec['authors'][:1]} differs from registry {entry.get('first_author')}"); return None
    if not year_ok(entry, rec):
        log.append(f"efetch by PMID {pmid}: year {rec['year']} differs from registry {entry.get('year')}"); return None
    log.append(f"efetch by PMID {pmid}: 1 record; DOI, first author, year{', title' if entry.get('title') else ''} agree")
    return rec, "PubMed by PMID"


def try_pubmed_doi(entry, log):
    doi = entry.get("doi")
    if not doi:
        return None
    s, err = pubmed_search(f'"{doi}"[AID] OR "{doi}"[LID] OR "{doi}"', f"{entry['id']}_pubmed_doi_esearch.json")
    if err:
        log.append(f"esearch by DOI {doi}: {err}"); return None
    if s["count"] == 0:
        log.append(f"esearch by DOI {doi}: 0 results"); return None
    recs, err = pubmed_fetch(s["ids"][:5], f"{entry['id']}_pubmed_doi_efetch.xml")
    if err:
        log.append(f"efetch after DOI search: {err}"); return None
    hits = [r for r in recs if (r.get("doi") or "").lower() == doi.lower()]
    if len(hits) != 1:
        log.append(f"esearch by DOI {doi}: {s['count']} result(s), {len(hits)} with that exact DOI"); return None
    rec = hits[0]
    if entry.get("title") and norm_title(entry["title"]) != norm_title(rec["title"]):
        log.append(f"esearch by DOI {doi}: DOI resolves but title differs from registry title"); return None
    if not first_author_ok(entry, rec) or not year_ok(entry, rec):
        log.append(f"esearch by DOI {doi}: DOI resolves but first author/year differ from registry"); return None
    log.append(f"esearch by DOI {doi}: exactly 1 record with that DOI; first author, year{', title' if entry.get('title') else ''} agree")
    return rec, "PubMed by DOI"


def try_pubmed_title(entry, log):
    title = entry.get("title")
    if not title:
        return None
    s, err = pubmed_search(f'"{title}"[Title]', f"{entry['id']}_pubmed_title_esearch.json")
    if err:
        log.append(f"esearch by title: {err}"); return None
    if s["count"] == 0:
        log.append("esearch by quoted title returned 0 results")
        words = [w for w in re.sub(r"[^A-Za-z0-9 ]+", " ", title).split() if len(w) > 2 and w.lower() not in PUBMED_STOPWORDS]
        s, err = pubmed_search(" AND ".join(f"{w}[ti]" for w in words), f"{entry['id']}_pubmed_title_words_esearch.json")
        if err:
            log.append(f"esearch by title words: {err}"); return None
        if s["count"] == 0:
            log.append("esearch by title words (all words AND, [ti]) returned 0 results"); return None
    recs, err = pubmed_fetch(s["ids"][:10], f"{entry['id']}_pubmed_title_efetch.xml")
    if err:
        log.append(f"efetch after title search: {err}"); return None
    hits = [r for r in recs if norm_title(r["title"]) == norm_title(title)]
    if len(hits) != 1:
        note_cands("PubMed", recs)
        log.append(f"esearch by title: {s['count']} result(s); {len(hits)} with an exactly matching normalised title"); return None
    rec = hits[0]
    if not doi_ok(entry, rec):
        log.append("esearch by title: title matches but record DOI differs from registry DOI"); return None
    if not first_author_ok(entry, rec) or not year_ok(entry, rec):
        log.append(f"esearch by title: title matches but first author/year differ (record: {rec['authors'][:1]}, {rec['year']})"); return None
    log.append(f"esearch by title: {s['count']} result(s); exactly 1 with an identical normalised title; first author and year agree")
    return rec, "PubMed by title"


def build_author_query(entry):
    parts = []
    if entry.get("first_author"):
        parts.append(f"{entry['first_author']}[1au]")
    if entry.get("year"):
        parts.append(f"{entry['year']}[dp]")
    if entry.get("journal"):
        parts.append(f'"{entry["journal"]}"[ta]')
    if entry.get("volume"):
        parts.append(f"{entry['volume']}[vi]")
    if entry.get("first_page"):
        parts.append(f"{entry['first_page']}[pg]")
    for k in entry.get("keywords") or []:
        parts.append(f'"{k}"[tiab]' if " " in k else f"{k}[tiab]")
    return " AND ".join(parts)


def try_pubmed_author(entry, log):
    if entry.get("title") or entry.get("doi") or entry.get("pmid"):
        return None  # only for entries with nothing better
    q = build_author_query(entry)
    q += ERRATA
    if not q or not entry.get("first_author"):
        if q:
            s, err = pubmed_search(q, f"{entry['id']}_pubmed_journal_kw_esearch.json")
            log.append(f"esearch by journal/year/keywords [{q}]: " + (err or f"{s['count']} result(s); not acceptable by rule (no first author in registry)"))
            if not err and 0 < s["count"] <= 5:
                recs, err2 = pubmed_fetch(s["ids"], f"{entry['id']}_pubmed_journal_kw_efetch.xml")
                if not err2:
                    note_cands("PubMed", recs)
        return None
    s, err = pubmed_search(q, f"{entry['id']}_pubmed_author_esearch.json")
    if err:
        log.append(f"esearch by author/year [{q}]: {err}"); return None
    if s["count"] != 1:
        if 0 < s["count"] <= 5:
            recs, err2 = pubmed_fetch(s["ids"], f"{entry['id']}_pubmed_author_cands_efetch.xml")
            if not err2:
                note_cands("PubMed", recs)
        log.append(f"esearch by author/year [{q}]: {s['count']} result(s) — not exactly one, rejected"); return None
    recs, err = pubmed_fetch(s["ids"], f"{entry['id']}_pubmed_author_efetch.xml")
    if err or len(recs) != 1:
        log.append(f"efetch after author/year search: {err or len(recs)}"); return None
    rec = recs[0]
    checks = {"first author": first_author_ok(entry, rec), "year": year_ok(entry, rec), "journal": journal_match(entry.get("journal"), rec)}
    if not all(checks.values()):
        log.append(f"esearch by author/year [{q}]: 1 result but {[k for k, v in checks.items() if not v]} do not match"); return None
    basis = "author+year+journal" if entry.get("journal") else "author+year+keywords"
    log.append(f"esearch by author/year [{q}]: exactly 1 result; first author, year{', journal' if entry.get('journal') else ''} agree")
    return rec, f"PubMed by {basis} (unique candidate; lower confidence)"


def try_crossref_doi(entry, log):
    doi = entry.get("doi")
    if not doi:
        return None
    d, err = crossref(f"{entry['id']}_crossref_doi.json", path="/" + urllib.parse.quote(doi, safe=""))
    if err or not d or d.get("status") != "ok":
        log.append(f"Crossref /works/{doi}: {err or 'no record'}"); return None
    rec = parse_crossref_item(d["message"])
    if (rec["doi"] or "").lower() != doi.lower():
        log.append(f"Crossref /works/{doi}: returned a different DOI"); return None
    if entry.get("title") and norm_title(entry["title"]) != norm_title(rec["title"]):
        log.append(f"Crossref /works/{doi}: DOI resolves but title differs from registry title"); return None
    if not first_author_ok(entry, rec) or not year_ok(entry, rec):
        log.append(f"Crossref /works/{doi}: DOI resolves but first author/year differ"); return None
    log.append(f"Crossref /works/{doi}: resolves; first author, year{', title' if entry.get('title') else ''} agree")
    return rec, "Crossref by DOI"


def try_crossref_title(entry, log):
    title = entry.get("title")
    if not title:
        return None
    d, err = crossref(f"{entry['id']}_crossref_title.json", **{"query.bibliographic": title, "rows": 5})
    if err or not d:
        log.append(f"Crossref by title: {err}"); return None
    items = [parse_crossref_item(i) for i in d.get("message", {}).get("items", [])]
    hits = [r for r in items if norm_title(r["title"]) == norm_title(title)]
    if len(hits) != 1:
        top = items[0]["title"][:80] if items else "none"
        log.append(f"Crossref by title: {len(items)} candidates, {len(hits)} with identical normalised title (top hit title: '{top}')"); return None
    rec = hits[0]
    if not doi_ok(entry, rec) or not first_author_ok(entry, rec) or not year_ok(entry, rec):
        log.append("Crossref by title: title matches but DOI/first author/year differ"); return None
    log.append("Crossref by title: exactly 1 of 5 candidates has an identical normalised title; first author and year agree")
    return rec, "Crossref by title"


def try_crossref_author(entry, log):
    if entry.get("title") or entry.get("doi") or entry.get("pmid") or not entry.get("first_author"):
        return None
    q = " ".join([entry["first_author"], str(entry.get("year") or ""), entry.get("journal") or "", *(entry.get("keywords") or [])]).strip()
    params = {"query.bibliographic": q, "rows": 5}
    params["query.author"] = entry["first_author"]
    d, err = crossref(f"{entry['id']}_crossref_author.json", **params)
    if err or not d:
        log.append(f"Crossref by author/year [{q}]: {err}"); return None
    items = [parse_crossref_item(i) for i in d.get("message", {}).get("items", [])]
    kws = [norm_title(k) for k in (entry.get("keywords") or [])]
    hits = [r for r in items if first_author_ok(entry, r) and year_ok(entry, r) and journal_match(entry.get("journal"), r)
            and all(k in norm_title(r["title"]) for k in kws)]
    titles = "; ".join(f"'{r['title'][:70]}' ({r['year']}, {r.get('type')})" for r in hits) or "none"
    if len(hits) != 1:
        note_cands("Crossref (author query)", [r for r in items if first_author_ok(entry, r)] or items, limit=3)
        log.append(f"Crossref by author/year [{q}]: {len(items)} candidates, {len(hits)} pass first-author+year+keyword filter — not exactly one, rejected ({titles})")
        # second attempt: keywords only in query.bibliographic, more rows, same strict filter
        kwq = " ".join(entry.get("keywords") or [])
        if kwq:
            d2, err2 = crossref(f"{entry['id']}_crossref_keywords.json", **{"query.bibliographic": kwq, "rows": 10})
            if err2 or not d2:
                log.append(f"Crossref by keywords [{kwq}]: {err2}"); return None
            items2 = [parse_crossref_item(i) for i in d2.get("message", {}).get("items", [])]
            hits2 = [r for r in items2 if first_author_ok(entry, r) and year_ok(entry, r) and journal_match(entry.get("journal"), r)
                     and all(k in norm_title(r["title"]) for k in kws)]
            note_cands("Crossref (keyword query)", [r for r in items2 if first_author_ok(entry, r)], limit=3)
            t2 = "; ".join(f"'{r['title'][:70]}' ({r['year']}, {r.get('type')})" for r in hits2) or "none"
            if len(hits2) != 1:
                log.append(f"Crossref by keywords [{kwq}]: {len(items2)} candidates, {len(hits2)} pass first-author+year+keyword filter — not exactly one, rejected ({t2})"); return None
            log.append(f"Crossref by keywords [{kwq}]: {len(items2)} candidates, exactly 1 passes first-author+year+keyword filter: {t2}")
            return hits2[0], "Crossref by author+year+keywords (unique candidate; lower confidence)"
        return None
    log.append(f"Crossref by author/year [{q}]: {len(items)} candidates, exactly 1 passes first-author+year+keyword filter: {titles}")
    return hits[0], "Crossref by author+year+keywords (unique candidate; lower confidence)"


STRATEGIES = [try_pubmed_pmid, try_pubmed_doi, try_pubmed_title, try_pubmed_author,
              try_crossref_doi, try_crossref_title, try_crossref_author]


# ----------------------------------------------------------------------------- main
def fmt_ref(rec):
    auth = ", ".join(rec["authors"]) if rec["authors"] else "(no authors returned)"
    vol = rec.get("volume") or "—"
    iss = f"({rec['issue']})" if rec.get("issue") else ""
    return (f"- **Authors:** {auth}\n- **Title:** {rec['title']}\n- **Journal:** {rec.get('journal') or rec.get('journal_abbrev') or '—'}"
            f"{' (' + rec['journal_abbrev'] + ')' if rec.get('journal_abbrev') and rec.get('journal') else ''}"
            f"{'; event: ' + rec['event'] if rec.get('event') else ''}\n- **Year:** {rec.get('year') or '—'}"
            f"\n- **Volume(issue):pages:** {vol}{iss}:{rec.get('pages') or '—'}\n- **DOI:** {rec.get('doi') or '—'}\n- **PMID:** {rec.get('pmid') or '—'}")


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    reg = yaml.safe_load(REG.read_text())["entries"]
    verified, unresolved = [], []
    for e in reg:
        log = []
        result = None
        _cands.clear()
        for strat in STRATEGIES:
            try:
                result = strat(e, log)
            except Exception as ex:  # never let one entry kill the run
                log.append(f"{strat.__name__}: exception {type(ex).__name__}")
                result = None
            if result:
                break
        if result:
            rec, src = result
            if rec["source_db"] == "Crossref" and rec.get("doi") and not rec.get("pmid"):
                s_, err_ = pubmed_search(f'"{rec["doi"]}"[AID] OR "{rec["doi"]}"', f"{e['id']}_pubmed_pmid_enrich_esearch.json")
                if not err_ and s_["count"] >= 1:
                    recs_, err2_ = pubmed_fetch(s_["ids"][:5], f"{e['id']}_pubmed_pmid_enrich_efetch.xml")
                    hits_ = [r for r in (recs_ or []) if (r.get("doi") or "").lower() == rec["doi"].lower() and norm_title(r["title"]) == norm_title(rec["title"])]
                    if len(hits_) == 1:
                        rec["pmid"] = hits_[0]["pmid"]
                        log.append(f"PMID {rec['pmid']} added from PubMed by DOI (DOI and normalised title agree with the Crossref record)")
                    else:
                        log.append(f"PubMed by DOI for PMID enrichment: {len(hits_)} record(s) with matching DOI and title; PMID left blank")
                else:
                    log.append("PubMed by DOI for PMID enrichment: " + (err_ or "0 results") + "; PMID left blank")
            verified.append({"id": e["id"], "confirmed_by": src, "record": rec, "attempts": log,
                             "repo_string": e.get("repo_string"), "repo_files": e.get("repo_files"), "search_basis": e.get("search_basis")})
        else:
            unresolved.append({"id": e["id"], "attempts": log, "repo_string": e.get("repo_string"), "brief_string": e.get("brief_string"),
                               "repo_files": e.get("repo_files"), "search_basis": e.get("search_basis"), "note": e.get("note"),
                               "candidates": list(dict.fromkeys(_cands))})
        print(f"{e['id']}: {'VERIFIED via ' + result[1] if result else 'UNRESOLVED'}")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # ---- verified_references.md
    L = [f"# Verified references — run_2026-09-19 Phase 10.4\n",
         f"Generated {now} by `scripts/verify_citations.py` from `docs/references/registry.yaml`. Every field below is copied from the "
         "PubMed (efetch XML) or Crossref (REST JSON) response that confirmed the entry; nothing is written from memory. "
         "Raw responses: `data/processed/run_2026-09-19_scratch/citations/` (untracked). Entries marked *lower confidence* were matched "
         "on first author + year (+ journal / keywords) with exactly one candidate returned, because the repo gives no title or identifier; "
         "Kyle should eyeball those before they go in a manuscript.\n"]
    for v in verified:
        L.append(f"## {v['id']}\n")
        L.append(f"- **Confirmed by:** {v['confirmed_by']}")
        L.append(f"- **As cited in repo:** {v['repo_string'] or '(not in repo; from task brief)'}  \n  files: {', '.join('`'+f+'`' for f in v['repo_files'] or []) or '—'}")
        L.append(fmt_ref(v["record"]))
        L.append("- **Trail:** " + " | ".join(v["attempts"]) + "\n")
    OUT_VERIFIED.write_text("\n".join(L))
    # ---- unresolved.md
    U = [f"# Unresolved references — run_2026-09-19 Phase 10.4\n",
         f"Generated {now} by `scripts/verify_citations.py`. Each entry lists exactly what was tried and what came back. "
         "No guess is recorded; these need a human decision or a fuller citation string in the source document.\n"]
    for u in unresolved:
        U.append(f"## {u['id']}\n")
        U.append(f"- **As cited in repo:** {u['repo_string'] or '(not in repo)'}  \n  files: {', '.join('`'+f+'`' for f in u['repo_files'] or []) or '—'}")
        if u.get("brief_string"):
            U.append(f"- **As named in the task brief:** {u['brief_string']}")
        if u.get("note"):
            U.append(f"- **Registry note:** {u['note']}")
        U.append("- **Tried:**")
        U.extend(f"  {i}. {a}" for i, a in enumerate(u["attempts"], 1))
        if u["candidates"]:
            U.append("- **Candidates returned by the APIs (NOT accepted — human review only; fields copied from the API response):**")
            U.extend(f"  - {c}" for c in u["candidates"])
        U.append("")
    OUT_UNRESOLVED.write_text("\n".join(U))
    # ---- counts
    by_src = {}
    for v in verified:
        by_src[v["confirmed_by"]] = by_src.get(v["confirmed_by"], 0) + 1
    out = {"generated_utc": now, "registry_size": len(reg), "verified": len(verified), "verified_by_source": by_src,
           "unresolved": len(unresolved), "unresolved_ids": [u["id"] for u in unresolved],
           "verified_ids": {v["id"]: {"confirmed_by": v["confirmed_by"], "doi": v["record"].get("doi"), "pmid": v["record"].get("pmid")} for v in verified},
           "search_basis": {e["id"]: e.get("search_basis") for e in reg}}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: out[k] for k in ("registry_size", "verified", "verified_by_source", "unresolved")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
