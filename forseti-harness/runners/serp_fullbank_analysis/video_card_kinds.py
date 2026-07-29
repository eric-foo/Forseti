r"""F22 derivation: what KIND of video is each platform's video card?

Two layers, applied in order:
 1. keyword tiers (deterministic) over every unique video_block card;
 2. for cards no keyword tier catches, the cached semantic verdicts in
    analysis/video_residue_classified.json (produced by a one-shot model
    pass 2026-07-29 over the 441-card residue; judged by meaning, cached
    so replays are deterministic).

Writes analysis/fullbank_video_card_kinds.json with the combined
per-platform distribution. Cards absent from the residue cache (e.g.
after new captures land) count as UNCACHED_RESIDUE rather than being
silently dropped -- a nonzero count means the semantic pass needs a
refresh, not that the numbers are complete.

Store path is operator-drive-pinned like the rest of this directory.
"""
import json
import glob
import re
import sys
import collections
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")

KINDS = [
    ("dupe/alternative", r"\bdupe|alternativ|instead of|cheaper|budget|drugstore\b"),
    ("head-to-head", r"\bvs\.?\b|versus|compar|which (one|is better)|better than"),
    ("warning/negative", r"\bavoid|don'?t buy|stop using|mistake|problem|issue|"
                         r"side effect|broke me out|purge|reaction|irritat|"
                         r"waste of|overrated|scam|not worth|ruin|ban\b|banned"),
    ("review/verdict", r"\breview|honest|worth (it|your money|the hype|spending)|"
                       r"first impress|testing|tried|tested|results|"
                       r"before and after|\d+ (day|week|month)|"
                       r"hype|verdict|thoughts on"),
    ("how-to/tutorial", r"\bhow to|how i|tutorial|guide|routine|apply|use\b|"
                        r"step|fix\b|tips|troubleshoot|solution|"
                        r"what am i doing wrong"),
    ("roundup/ranking", r"\bbest\b|top \d|\d+ (best|products|picks)|favou?rites|"
                        r"ranking|ranked|tier list"),
    ("praise/endorsement", r"\bobsessed|love (this|my|it)|holy grail|"
                           r"game.?changer|amazing|my favou?rite|"
                           r"can'?t live without|need (this|to try)|"
                           r"you need|glow(y|ing)?\b|in love|"
                           r"the best (thing|purchase)|staple\b"),
    ("commiseration/relatable", r"\bvictimi[sz]ed|raise your hand|"
                                r"struggling|struggle|anyone else|"
                                r"is it just me|we'?ve all|pov:?|"
                                r"when you|that feeling"),
    ("promo/brand-copy", r"\bshop now|link in bio|available (now|at)|"
                         r"new (launch|drop)|introducing|"
                         r"continuously plumps|discover\b|"
                         r"welcome to\b|when it comes to\b"),
    ("question-hook", r"\?\s*$|^\s*(is|are|do|does|should|can|will|what|why|"
                      r"which|did)\b.*\?"),
]
RX = [(k, re.compile(p, re.I)) for k, p in KINDS]


def keyword_kind(title):
    for k, rx in RX:
        if rx.search(title):
            return k
    return None


def main():
    residue = {}
    cache_path = ROOT / "analysis" / "video_residue_classified.json"
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        for c in cached["cards"]:
            residue[(c["platform"], c["creator"], c["title"])] = c["category"]

    per = {p: collections.Counter() for p in ("tiktok", "instagram", "youtube")}
    seen = set()
    for f in glob.glob(str(ROOT / "extracted_v2" / "*.json")):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        for r in d.get("rows", []):
            if r.get("module_type") != "video_block":
                continue
            dom = (r.get("displayed_domain") or "").lower()
            plat = next((p for p in per if p in dom), None)
            if not plat:
                continue
            a, t = r.get("account_or_creator") or "", r.get("title") or ""
            if (plat, a, t) in seen:
                continue
            seen.add((plat, a, t))
            kind = keyword_kind(t) or residue.get((plat, a, t)) \
                or "UNCACHED_RESIDUE"
            per[plat][kind] += 1

    out = {"method": "keyword tiers, then cached semantic verdicts for the "
                     "residue; UNCACHED_RESIDUE>0 means the semantic cache "
                     "is stale for the current corpus",
           "platforms": {}}
    for p, c in per.items():
        n = sum(c.values())
        out["platforms"][p] = {
            "n_unique_cards": n,
            "kinds": {k: {"count": v, "share": round(v / n, 3)}
                      for k, v in c.most_common()},
        }
        print(f"{p:10s} n={n:4d}  top: " + ", ".join(
            f"{k} {v/n:.0%}" for k, v in c.most_common(4)))
        if c["UNCACHED_RESIDUE"]:
            print(f"  !! {c['UNCACHED_RESIDUE']} uncached residue cards -- "
                  f"semantic pass needs refresh")
    (ROOT / "analysis" / "fullbank_video_card_kinds.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote analysis/fullbank_video_card_kinds.json")


if __name__ == "__main__":
    main()
