r"""Do vs_rival / dupe / alternatives cannibalise each other?

The claim arrived from a concurrent lane (competitor_ledger_spec_v0.md,
2026-07-29) citing a figure that appears in no sealed output. Rather than
rehome an assertion, test it two ways against the durable store:

 1. MUTUAL OVERLAP -- within subjects carrying all three, the pairwise
    question-set Jaccard among the trio, against the same statistic for
    all other shape pairs. Cannibalising shapes should overlap more than
    unrelated ones (this is how F5 established the review family).
 2. DESIGN CONTRAST -- `alternatives` unique share in the P11 design
    (which also carries vs_rival AND dupe) against the P9 design (which
    carries neither). If the trio cannibalises, removing two members
    should RAISE the third's unique share.

Writes analysis/fullbank_shape_cannibalisation.json.
Store path operator-drive-pinned like the rest of this directory.
"""
import json
import sys
import collections
import itertools
import statistics
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
EX = ROOT / "extracted_v2"
TRIO = ("vs_rival", "dupe", "alternatives")

bank = json.loads((ROOT / "query_bank.json").read_text(encoding="utf-8"))
subj_shape = collections.defaultdict(dict)
for j in bank:
    if not j.get("twin_leg"):
        subj_shape[j["subject"]][j["shape"]] = j["job_id"]


def questions(jid):
    p = EX / f"{jid}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    qs = {r["title"].strip().lower() for r in d.get("rows", [])
          if r["module_type"] in ("people_also_ask", "related_search")
          and r.get("title")}
    return qs or None


def jac(a, b):
    return len(a & b) / len(a | b) if (a | b) else None


# ---- 1. mutual overlap --------------------------------------------------
trio_pairs, other_pairs = [], []
n_subjects = 0
for subj, shapes in subj_shape.items():
    qs = {}
    for sh, jid in shapes.items():
        q = questions(jid)
        if q:
            qs[sh] = q
    if not all(t in qs for t in TRIO):
        continue
    n_subjects += 1
    for a, b in itertools.combinations(sorted(qs), 2):
        v = jac(qs[a], qs[b])
        if v is None:
            continue
        if a in TRIO and b in TRIO:
            trio_pairs.append(v)
        else:
            other_pairs.append(v)

overlap = {
    "n_subjects_with_all_three": n_subjects,
    "trio_pairwise_jaccard": {
        "n": len(trio_pairs),
        "mean": round(statistics.mean(trio_pairs), 3) if trio_pairs else None,
        "median": round(statistics.median(trio_pairs), 3) if trio_pairs else None},
    "all_other_pairwise_jaccard": {
        "n": len(other_pairs),
        "mean": round(statistics.mean(other_pairs), 3) if other_pairs else None,
        "median": round(statistics.median(other_pairs), 3) if other_pairs else None},
}

# ---- 2. design contrast -------------------------------------------------
fd = json.loads((ROOT / "analysis" / "fullbank_fixed_design.json")
                .read_text(encoding="utf-8"))
contrast = {}
for design in ("P11", "P9"):
    d = fd.get(design, {})
    shapes = set(d.get("shapes", []))
    fb = (d.get("questions") or {}).get("fullbank") or {}
    alt = fb.get("alternatives")
    contrast[design] = {
        "carries_vs_rival": "vs_rival" in shapes,
        "carries_dupe": "dupe" in shapes,
        "alternatives_unique_share": alt.get("uniq") if alt else None,
        "n_shapes": len(shapes),
    }

out = {
    "artifact": "fullbank_shape_cannibalisation",
    "claim_under_test": "the vs/dupe/alternatives shapes cannibalise each "
                        "other when co-present, leaving `alternatives` "
                        "under-credited (arrived from a concurrent lane, "
                        "2026-07-29, citing an unsealed figure)",
    "mutual_overlap": overlap,
    "design_contrast": contrast,
    "confound": "P11 and P9 differ by TWO shapes and in shape-set size; "
                "unique share is depressed by a larger competing set, so a "
                "P11<P9 gap is expected from set size alone and is not by "
                "itself evidence of cannibalisation",
}
(ROOT / "analysis" / "fullbank_shape_cannibalisation.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"subjects carrying all three: {n_subjects}")
print(f"  trio pairwise question overlap : "
      f"mean {overlap['trio_pairwise_jaccard']['mean']} "
      f"(n={overlap['trio_pairwise_jaccard']['n']})")
print(f"  all other pairs                : "
      f"mean {overlap['all_other_pairwise_jaccard']['mean']} "
      f"(n={overlap['all_other_pairwise_jaccard']['n']})")
for k, v in contrast.items():
    print(f"  {k}: alternatives uniq={v['alternatives_unique_share']} "
          f"(vs_rival={v['carries_vs_rival']}, dupe={v['carries_dupe']}, "
          f"{v['n_shapes']} shapes)")
