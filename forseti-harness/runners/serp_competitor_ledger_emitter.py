"""Competitor ledger emitter v0.3 (Channel 0: free-rider harvest).

Harvests typed competitor candidates from already-captured SERP
extractions — related searches, PAA, organic/video titles, AIO text.
Types, ladder, and channels: competitor_ledger_spec_v0.md (staging).
Presence-only signal: citing, never switching; counts of observed
surfaces only. finding_grade is unreachable from SERP alone (needs a
second surface class) — by design.

v0.1 (Tower 28 trial lessons): brand-token subject matching (category
words like "concealer" no longer claim the wrong side), outlet/creator
names routed to a mediators list instead of the ledger, community
"X or Y" pattern, imperative/use-context junk rejection.

v0.2 (full-bank adjudication lessons): enumerated peer-list recall
(comma series carried no split cue and 70 titles yielded nothing), and
a brand-or-not promotion gate (--verdicts): recurrence AMPLIFIES common
English, so the candidate rung is only reachable through a cached
adjudication verdict; unadjudicated recurrers hold at
pending_adjudication, fail closed.

v0.3 (queue-completion adjudication): trailing use-context compounds
collapse to their parent entity, condition-only names fail closed,
possessive apostrophes normalize for subject matching, and adjudicated
self variants carry their ratified type.

Two modes:
  (default)          megadogfood store: run_ledger + query_bank drive
                     subject/query per extraction; issue subjects skipped.
  --extractions DIR --subject NAME [--subject NAME2 ...]
                     Understanding-cycle scout mode: scan a directory of
                     extract_serp_v2 JSONs; query comes from each packet's
                     requested_query; harvest only the named subject(s).
Optional --output FILE overrides the default ledger path.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")

STOP = {"the", "a", "an", "of", "for", "and", "or", "with", "my", "your",
        "best", "top", "good", "better", "new", "review", "reviews"}
EXCLUDE = {"sephora", "ulta", "amazon", "walmart", "target", "nordstrom",
           "cvs", "walgreens", "costco", "boots", "reddit", "tiktok",
           "youtube", "instagram", "facebook", "pinterest", "google",
           "drugstore", "dupe", "dupes", "alternative", "alternatives",
           "each other", "one", "it", "them", "other", "others", "vs"}
# category/product words never establish subject identity on their own
GENERIC_PRODUCT = {
    "concealer", "cream", "sunscreen", "spray", "serum", "moisturizer",
    "moisturizing", "cleanser", "mask", "balm", "lip", "treatment",
    "powder", "oil", "shampoo", "conditioner", "lotion", "gel", "toner",
    "mascara", "foundation", "lipstick", "gloss", "tint", "primer",
    "blush", "bronzer", "spf", "press", "maker", "machine", "grinder",
    "supplement", "greens", "ointment", "wash", "scrub", "peel", "drops",
    "healing", "sleeping", "hydrating"}
# use-context words: a name made only of these is a context, not an entity
CONTEXT_GENERIC = {
    "skin", "hair", "face", "acne", "dry", "oily", "sensitive",
    "combination", "prone", "mature", "teen", "teens", "beginners",
    "budget", "any", "all", "summer", "winter", "baby", "men", "women",
    "kids", "everyday", "daily", "version", "body", "hand", "foot",
    "eye", "night", "day", "irritated", "wound", "wounds", "scar",
    "scars", "lips", "aging", "wrinkles", "fine", "curly"}

VS_RX = re.compile(r"\s+(?:vs\.?|versus)\s+", re.I)
OR_RX = re.compile(r"\s+or\s+", re.I)
# v0.2 recall: enumerated peer lists ("... : Beauty of Joseon, Isntree,
# Round Lab, Skin1004"). Full-bank sizing found 93 such titles, 70 of
# which produced zero ledger entries because none of the four split cues
# fires on a comma series.
ENUM_MIN_PARTS = 3
BETTER_RX = re.compile(r"better than\s+(.+?)(?:[?.!]|$)", re.I)
DUPE_FOR_RX = re.compile(r"(.+?)\s+dupes?\s+for\s+(.+)", re.I)
QUESTION_START = re.compile(
    r"^(what|which|who|how|why|is|are|does|do|can|where|when)\b", re.I)
IMPERATIVE_START = re.compile(
    r"^(recommend|find|get|try|shop|discover|meet|check|see|watch|use|"
    r"stop|buy|grab|introducing|top|best)\b", re.I)
OUTLET_RX = re.compile(
    r"\bon\s+(instagram|tiktok|youtube|facebook|pinterest)\b", re.I)
OBVIOUS_FRAGMENT_RX = re.compile(
    r"^(?:good|bad|benefits?)$|^\d+(?:\s|$)|\breddit[- ]picked\b|"
    r"^(?:i|we|you|they|he|she)\s+|(?:\.\s*\d|\bwhy\b|[?!].+\w)",
    re.I,
)


def _norm(t):
    return re.sub(r"(?<=[a-z])\d+$", "", t)  # tower28 -> tower


def sig_tokens(s):
    # Straight/curly/missing possessive apostrophes must describe the same
    # brand token ("Paula's", "Paula’s", and "Paula").
    normalized = s.lower().replace("\u2019", "'")
    toks = {t for t in re.findall(r"[a-z0-9']+", normalized)
            if len(t) > 2 and t not in STOP}
    return toks | {_norm(t) for t in toks} | {
        re.sub(r"'s$", "", t) for t in toks}


def brand_tokens(subject):
    """Distinctive subject tokens: category/context words don't count."""
    toks = sig_tokens(subject) - GENERIC_PRODUCT - CONTEXT_GENERIC
    return toks or sig_tokens(subject)  # fall back for all-generic subjects


def matches_subject(text, brand_toks):
    return bool(sig_tokens(text) & brand_toks)


def clean(name):
    name = re.split(r"[:|(\[—–?]| - ", name)[0]
    name = re.sub(r"['’]s\b", "", name)          # possessive only
    name = re.sub(r"^better,\s*", "", name, flags=re.I)
    # strip leading question words + articles (keep the noun phrase:
    # "Is the NYX concealer a" -> "NYX concealer a"); imperatives reject
    for _ in range(4):
        stripped = re.sub(r"^(what|which|who|how|why|is|are|does|do|can|"
                          r"where|when|the|a|an|this|that|these|those)\s+",
                          "", name.strip(), flags=re.I)
        if stripped == name.strip():
            break
        name = stripped
    # Comparison questions can put the condition before a comma and the
    # entity after it ("better for irritated skin, Vaseline"). Retain the
    # entity only when the lead is entirely contextual.
    condition_lead = re.match(
        r"^(?:better|best|good)\s+for\s+([^,]+),\s*(.+)$", name, flags=re.I)
    if condition_lead:
        lead_toks = sig_tokens(condition_lead.group(1))
        if lead_toks and lead_toks <= (CONTEXT_GENERIC | GENERIC_PRODUCT):
            name = condition_lead.group(2)
    # Context suffixes are not separate entities. Collapse only when the
    # whole suffix is known context/category vocabulary; otherwise preserve
    # the candidate and fail visibly through the normal adjudication gate.
    context = re.search(r"\s+for\s+(.+)$", name, flags=re.I)
    if context:
        context_toks = sig_tokens(context.group(1))
        if context_toks and context_toks <= (
                CONTEXT_GENERIC | GENERIC_PRODUCT):
            name = name[:context.start()]
    name = re.sub(r"\s+(reddit|review|reviews|the|a|an)$", "", name, flags=re.I)
    name = name.strip(" .,!\"’-–—")
    words = name.split()
    if not (1 <= len(words) <= 6):
        return None
    if IMPERATIVE_START.match(name):
        return None
    if OBVIOUS_FRAGMENT_RX.search(name):
        return None
    toks = sig_tokens(name)
    if not toks or name.lower() in EXCLUDE:
        return None
    if toks <= (CONTEXT_GENERIC | GENERIC_PRODUCT):
        return None                              # pure context/category
    return name


def is_outlet(text):
    return bool(OUTLET_RX.search(text))


def pair_yield(parts, brand_toks, typ, surface, text):
    """For a comparison split (vs/or): sides not matching the subject."""
    matched = [matches_subject(p, brand_toks) for p in parts]
    if not any(matched):
        return
    for p, m in zip(parts, matched):
        if not m:
            name = clean(p)
            if name:
                yield name, typ, surface, text


def harvest(texts, subject, query):
    """Yield (name, type, surface, evidence) or ('MEDIATOR', name, ...)."""
    brand_toks = brand_tokens(subject)
    for surface, text in texts:
        if not text:
            continue
        if is_outlet(text) and matches_subject(text, brand_toks):
            m = OUTLET_RX.search(text)
            handle = text[:m.start()].strip(' "\u201c')
            if 0 < len(handle.split()) <= 4:
                yield "MEDIATOR", handle + " (" + m.group(1).lower() + ")", surface, text
            continue                             # outlets never enter the ledger
        parts = VS_RX.split(text)
        if len(parts) >= 2:
            yield from pair_yield(parts, brand_toks, "rival", surface, text)
        elif len(text.split()) <= 12:            # short community "X or Y?"
            parts = OR_RX.split(text)
            if len(parts) == 2:
                yield from pair_yield(parts, brand_toks, "rival", surface, text)
        m = BETTER_RX.search(text)
        if m and matches_subject(text[:m.start()], brand_toks):
            name = clean(m.group(1))
            if name:
                yield name, "rival", surface, text
        # "<Y> dupe for <X>": X≈subject → Y is dupe_association;
        # subject on the dupe side → X is the subject's anchor_up
        m = DUPE_FOR_RX.search(text)
        if m:
            left, right = m.group(1), m.group(2)
            l_sub, r_sub = (matches_subject(left, brand_toks),
                            matches_subject(right, brand_toks))
            if r_sub and not l_sub:
                name = clean(left)
                if name:
                    yield name, "dupe_association", surface, text
            elif l_sub and not r_sub:
                name = clean(right)
                if name:
                    yield name, "anchor_up", surface, text
        # v0.2: enumerated peer list. Same subject-anchoring rule as the
        # vs/or split: the title must reach the subject somewhere, and only
        # the non-subject parts yield. ENUM_MIN_PARTS comma segments keeps
        # ordinary prose commas out; per-part shape is clean()'s job.
        if matches_subject(text, brand_toks):
            tail = text.split(":", 1)[-1]
            parts = [p.strip() for p in tail.split(",")]
            if len(parts) >= ENUM_MIN_PARTS and \
                    all(0 < len(p.split()) <= 4 for p in parts if p):
                for p in parts:
                    if p and not matches_subject(p, brand_toks):
                        name = clean(p)
                        if name:
                            yield name, "rival", surface, text


def packet_texts(pkt):
    texts = []
    for r in pkt["rows"]:
        cls = ("serp_question_layer" if r["module_type"] in
               ("people_also_ask", "related_search") else "serp_result_title")
        texts.append((cls, r.get("title")))
    aio = pkt.get("ai_overview") or {}
    if aio.get("present"):
        texts.append(("serp_aio", " ".join(
            str(v) for v in aio.values() if isinstance(v, str))))
    return texts


def probes_megadogfood():
    """(subject, category, query, texts) per eligible megadogfood probe."""
    ledger_rows = [json.loads(l) for l in
                   (ROOT / "run_ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
    issue_subjects = {j["subject"] for j in bank
                      if j["subject_maturity"] == "issue"}
    for row in ledger_rows:
        if row["outcome"] != "ok" or row.get("twin_of"):
            continue
        if row["subject"] in issue_subjects:
            continue  # competitors are a product-subject concept (spec v0)
        p = ROOT / "extracted_v2" / f"{row['job_id']}.json"
        if not p.exists():
            continue
        pkt = json.loads(p.read_text(encoding="utf-8"))
        yield row["subject"], row["category"], row["query"], packet_texts(pkt)


def probes_scout(exdir, subjects):
    """Understanding-cycle scout mode: every extraction x every subject."""
    for p in sorted(Path(exdir).glob("*.json")):
        pkt = json.loads(p.read_text(encoding="utf-8"))
        query = pkt.get("requested_query") or pkt.get("rendered_query") or p.stem
        texts = packet_texts(pkt)
        for subject in subjects:
            yield subject, "cycle_scout", query, texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractions", help="dir of extract_serp_v2 JSONs (scout mode)")
    ap.add_argument("--subject", action="append", default=[],
                    help="subject name (scout mode; repeatable)")
    ap.add_argument("--output", help="output JSON path override")
    ap.add_argument("--verdicts",
                    help="adjudication cache JSON (v0.2 promotion gate). "
                         "Recurrence alone AMPLIFIES junk -- common English "
                         "recurs more reliably than any real brand -- so no "
                         "entry reaches the candidate rung without a cached "
                         "brand-or-not verdict. Unadjudicated entries hold at "
                         "pending_adjudication (fail closed), never candidate.")
    ap.add_argument("--mediator-classes",
                    help="mediator classification cache JSON. An anchor's "
                         "attachment (2+ days, F24) says nothing about its "
                         "KIND, and consumers act oppositely on a "
                         "professional_creator vs an affiliate_outlet vs a "
                         "brand_owned account. Uncached mediators emit "
                         "pending_classification (fail visible, like the "
                         "candidate gate).")
    args = ap.parse_args()

    verdict_gate = args.verdicts is not None
    verdicts = {}
    if verdict_gate and Path(args.verdicts).exists():
        vd = json.loads(Path(args.verdicts).read_text(encoding="utf-8"))
        verdicts = {(v["subject"], v["name"].lower()): v["verdict"]
                    for v in vd["verdicts"]}

    mediator_class_gate = args.mediator_classes is not None
    med_classes = {}
    if mediator_class_gate and Path(args.mediator_classes).exists():
        mc = json.loads(Path(args.mediator_classes).read_text(encoding="utf-8"))
        med_classes = {m["name"].lower(): m["class"]
                       for m in mc["mediators"]}

    if args.extractions:
        if not args.subject:
            ap.error("--extractions requires at least one --subject")
        probes_iter = probes_scout(args.extractions, args.subject)
        out_path = Path(args.output) if args.output else (
            Path(args.extractions).parent / "competitor_ledger_v0.json")
    else:
        probes_iter = probes_megadogfood()
        out_path = Path(args.output) if args.output else (
            ROOT / "analysis" / "competitor_ledger_v0.json")

    entries = defaultdict(lambda: {"sources": []})
    mediators = defaultdict(set)
    probes = 0
    for subject, category, query, texts in probes_iter:
        probes += 1
        for item in harvest(texts, subject, query):
            if item[0] == "MEDIATOR":
                mediators[item[1]].add(subject)
                continue
            name, typ, surface, evidence = item
            key = (subject, name.lower(), typ)
            e = entries[key]
            e.update({"name": name, "type": typ, "subject": subject,
                      "category": category, "seed": None})
            src = {"surface_class": surface, "query": query,
                   "evidence": evidence[:160]}
            if src not in e["sources"]:
                e["sources"].append(src)

    out = []
    for e in entries.values():
        queries = {s["query"] for s in e["sources"]}
        classes = {s["surface_class"] for s in e["sources"]}
        e["distinct_queries"] = len(queries)
        e["surface_classes"] = sorted(classes)
        recurs = len(queries) >= 2
        if not recurs:
            e["rung"] = "presence"
        elif not verdict_gate:
            e["rung"] = "candidate"          # v0.1 behavior: no gate supplied
        else:
            v = verdicts.get((e["subject"], e["name"].lower()))
            if v == "USABLE":
                e["rung"], e["verdict"] = "candidate", v
            elif v == "SELF_VARIANT":
                e["type"], e["rung"], e["verdict"] = (
                    "self_variant", "presence", v)
            elif v is None:
                e["rung"] = "pending_adjudication"
            else:                            # JUNK / RECOVERABLE
                e["rung"], e["verdict"] = "presence", v
        out.append(e)
    out.sort(key=lambda e: (-e["distinct_queries"], e["subject"], e["name"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"probes_scanned": probes, "entries": out,
               "mediators": {k: sorted(v) for k, v in
                             sorted(mediators.items())}}
    if mediator_class_gate:
        # Parallel map, not a shape change: existing consumers keep reading
        # mediators as name -> subjects.
        payload["mediator_classes"] = {
            k: med_classes.get(k.lower(), "pending_classification")
            for k in sorted(mediators)}
    out_path.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    n_cand = sum(1 for e in out if e["rung"] == "candidate")
    n_pend = sum(1 for e in out if e["rung"] == "pending_adjudication")
    print(f"probes scanned: {probes}; entries: {len(out)} "
          f"({n_cand} candidate, {n_pend} pending_adjudication, "
          f"{len(out) - n_cand - n_pend} presence); "
          f"mediators routed: {len(mediators)} -> {out_path}")
    if n_pend:
        print(f"!! {n_pend} recurring entries lack a brand-or-not verdict; "
              f"adjudicate and append to the verdicts cache, then re-run")
    by_type = defaultdict(int)
    for e in out:
        by_type[e["type"]] += 1
    print("by type:", dict(by_type))
    print("\n=== candidates (2+ distinct queries) ===")
    for e in out:
        if e["rung"] == "candidate":
            print(f"  {e['subject']:<28} {e['type']:<17} {e['name']:<30} "
                  f"q={e['distinct_queries']}")


if __name__ == "__main__":
    main()
