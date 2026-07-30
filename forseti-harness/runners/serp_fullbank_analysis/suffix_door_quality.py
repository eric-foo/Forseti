r"""Are the platform-suffix doors CI-worthy? Judge the already-captured
cards: content kind (keyword tier only), brand-own-account share, and
creator overlap with the 113-creator feed.

Seals analysis/fullbank_suffix_quality.json — the F23 quality-read
evidence, including the NAMED sets, not only their counts. The first
version sealed `creators_not_in_113_feed` as a bare integer, which the
YouTube onboarding pilot then could not act on: a count that cannot be
reconstructed into the thing it counts is a claim, not evidence, and two
readers normalising names differently get different totals with no way
to reconcile. The normalisation is now stated and applied explicitly. Kinds here are KEYWORD-TIER ONLY: the semantic residue cache
does not cover these cards, so the kind mix is partial by design and
says so. Store path operator-drive-pinned like the rest of this
directory.
"""
import json
import re
import sys
import collections
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import video_card_kinds as V  # noqa: E402

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
FEED = Path(__file__).resolve().parents[3] / "docs" / "research" / \
    "serp_lane_competitor_scout_20260728" / "serp_recurring_creator_feed_v0.json"

def norm_creator(name: str) -> str:
    """The ONLY creator-name normalisation this lane uses.

    Stated because it is load-bearing: feed membership is decided by string
    equality, so casefold/strip/whitespace choices move the totals. Casefold
    (not lower) so non-ASCII handles compare correctly; collapse internal
    whitespace; strip. Anything comparing creator names to the feed must use
    this function, or its counts will not reconcile with these.
    """
    return " ".join(str(name or "").split()).casefold()


bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
feed = json.loads(FEED.read_text(encoding="utf-8"))
known = {(r["platform"], norm_creator(r["display_name"]))
         for r in feed["creators"]}

SUFFIX = {"tiktok_suffix": "tiktok", "youtube_suffix": "youtube",
          "instagram_suffix": "instagram"}
BRAND_HINT = re.compile(
    r"cerave|cetaphil|ordinary|paula|byoma|bubble|medicube|anua|neutrogena|"
    r"laneige|rhode|glow recipe|supergoop|joseon|dieux|drunk elephant|"
    r"olaplex|dyson|torriden|skin1004|isntree|innisfree|kosas|eucerin|"
    r"aquaphor|cosrx|naturium|vaseline|biodance|round lab|tirtir|shark|"
    r"revlon|hoka|brooks|breville|aeropress|fellow|helix|purple|stanley|"
    r"quip|notion|ynab|ag1|bloom", re.I)
STOPTOK = {"dupe", "review", "honest", "vs", "best", "worth", "alternatives",
           "results", "problems", "working", "tiktok", "youtube",
           "instagram", "reddit"}


seal = {}
for shape, plat in SUFFIX.items():
    kinds = collections.Counter()
    creators = collections.Counter()
    new_creators = set()
    brandy = total = own = attributed = 0
    for j in bank:
        if j["shape"] != shape or j.get("twin_leg"):
            continue
        p = ROOT / "extracted_v2" / f"{j['job_id']}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        subj_toks = [w for w in re.findall(r"[a-z0-9]{3,}",
                                           j["subject"].lower())
                     if w not in STOPTOK]
        for r in d.get("rows", []):
            dom = (r.get("displayed_domain") or "").lower()
            if plat not in dom:
                continue
            t = r.get("title") or ""
            a = r.get("account_or_creator") or ""
            total += 1
            kinds[V.keyword_kind(t) or "needs-semantic-pass"] += 1
            if BRAND_HINT.search(t):
                brandy += 1
            if a:
                creators[a] += 1
                if (plat, norm_creator(a)) not in known:
                    new_creators.add(a)
                attributed += 1
                handle = re.sub(r"[^a-z0-9]", "", a.lower())
                if any(tok in handle for tok in subj_toks):
                    own += 1
    seal[shape] = {
        "platform_cards": total,
        "known_brand_titles": brandy,
        "known_brand_title_share": round(brandy / total, 3) if total else None,
        "attributed_cards": attributed,
        "own_account_cards": own,
        "own_account_share": round(own / attributed, 3) if attributed else None,
        "distinct_creators": len(creators),
        "creators_not_in_113_feed": len(new_creators),
        # The NAMED set, so the count is reconstructible and a consumer can
        # act on it. Sorted for a stable diff across re-runs.
        "creators_not_in_113_feed_names": sorted(new_creators),
        "kinds_keyword_tier_only": dict(kinds),
    }
    print(f"{shape:18s} cards={total:4d} brand-titles={brandy/total:.0%} "
          f"own-account={own/attributed:.0%} creators={len(creators)} "
          f"new-vs-feed={len(new_creators)}")

out = {
    "artifact": "fullbank_suffix_quality",
    "derivation": "suffix_door_quality.py over extracted_v2 suffix probes",
    "own_account_heuristic": "creator handle contains a non-generic subject "
                             "token; undercounts brand accounts for OTHER "
                             "subjects, never overcounts the subject's own",
    "creator_name_normalisation": "norm_creator(): collapse internal "
                                  "whitespace, strip, casefold. Feed "
                                  "membership is string equality, so a "
                                  "consumer using different normalisation "
                                  "WILL get different totals - use this "
                                  "function to reconcile.",
    "kinds_caveat": "keyword tier only; the semantic residue cache does not "
                    "cover these cards, so needs-semantic-pass is large by "
                    "design",
    "shapes": seal,
}
(ROOT / "analysis" / "fullbank_suffix_quality.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote analysis/fullbank_suffix_quality.json")
