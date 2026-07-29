"""Hand adjudication of the 111 candidate-rung entries in the full-bank ledger.

Buckets (one per entry; the emitter is not edited, this only sizes the fix):
  USABLE       a real third-party entity name, ready for a cycle N+1 vs probe
  RECOVERABLE  a real name the current emitter mangles — a compound, comma
               artifact, or truncation that a repaired emitter would collapse
               onto a name ALREADY in the ledger or trivially recoverable
  SELF_VARIANT the subject's own line (the open owner vocabulary question)
  JUNK         category/use-context word or prose fragment; no entity at all
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

AN = Path(r"C:\tmp\forseti-serp-megadogfood-20260727\analysis")

VERDICT = {
 ("aeropress", "French Press"): "JUNK",            # brew method, not a brand
 ("aeropress", "Premium"): "SELF_VARIANT",         # AeroPress Premium
 ("aeropress", "ORB"): "USABLE",
 ("aeropress", "Delter Press"): "USABLE",
 ("aeropress", "Trinity Zero"): "USABLE",
 ("aeropress", "Cafetiere / French Press. Amazing"): "JUNK",
 ("aeropress", "Nanopress"): "USABLE",
 ("aeropress", "Oxo Brewer"): "USABLE",
 ("aeropress", "pour over"): "JUNK",
 ("ag1 greens powder", "Live it Up"): "USABLE",
 ("anua heartleaf toner", "Pads"): "JUNK",
 ("anua heartleaf toner", "original"): "SELF_VARIANT",
 ("aquaphor healing ointment", "Vaseline"): "USABLE",
 ("aquaphor healing ointment", "Irritated Skin"): "JUNK",
 ("aquaphor healing ointment", "Neosporin"): "USABLE",
 ("aquaphor healing ointment", "Vaseline for baby"): "RECOVERABLE",
 ("aquaphor healing ointment", "Vaseline for wound healing"): "RECOVERABLE",
 ("aquaphor healing ointment", "better, Vaseline"): "RECOVERABLE",
 ("aquaphor healing ointment", "CeraVe"): "USABLE",
 ("aquaphor healing ointment", "Cerave Healing Ointment"): "RECOVERABLE",
 ("aquaphor healing ointment", "Vaseline for face"): "RECOVERABLE",
 ("aquaphor healing ointment", "Petroleum Jelly"): "JUNK",   # ingredient class
 ("aquaphor healing ointment", "Vaseline for Dry Skin"): "RECOVERABLE",
 ("aquaphor healing ointment", "dermatologists prefer Vaseline"): "RECOVERABLE",
 ("beauty of joseon sunscreen", "Round Lab"): "USABLE",
 ("bloom greens powder", "better AG1"): "RECOVERABLE",
 ("breville barista express", "Bambino Plus"): "SELF_VARIANT",
 ("breville barista express", "DeLonghi Magnifica"): "USABLE",
 ("breville barista express", "Ninja Luxe"): "USABLE",
 ("breville barista express", "Generic Espresso Machine"): "JUNK",
 ("breville barista express", "Barista Express"): "SELF_VARIANT",
 ("breville barista express", "better, DeLonghi"): "RECOVERABLE",
 ("brooks ghost 15", "otherwise"): "JUNK",
 ("byoma moisturizer", "Cerave"): "USABLE",
 ("byoma moisturizer", "better, Cerave"): "RECOVERABLE",
 ("cerave moisturizing cream", "Amazon Basics"): "USABLE",
 ("cerave moisturizing cream", "Amazon Basics Moisturizing Cream really"): "RECOVERABLE",
 ("cerave moisturizing cream", "Irritated Skin"): "JUNK",
 ("cerave moisturizing cream", "better, Cetaphil"): "RECOVERABLE",
 ("cerave moisturizing cream", "chafing #skincareviral #Cerave #moisturizing"): "JUNK",
 ("cetaphil gentle cleanser", "better, CeraVe"): "RECOVERABLE",
 ("cetaphil gentle cleanser", "CeraVe"): "USABLE",
 ("cetaphil gentle cleanser", "dermatologists prefer CeraVe"): "RECOVERABLE",
 ("dieux instant angel moisturizer", "107 Reddit-Picked"): "JUNK",
 ("dieux instant angel moisturizer", "Aestura"): "USABLE",
 ("drunk elephant protini", "K-Beauty"): "JUNK",
 ("dyson airwrap", "Shark"): "USABLE",
 ("dyson airwrap", "Anyone know any good"): "JUNK",
 ("dyson airwrap", "It Dupes"): "JUNK",
 ("dyson airwrap", "Old Attachments"): "JUNK",
 ("dyson airwrap", "not"): "JUNK",
 ("eucerin advanced repair cream", "better, Cerave"): "RECOVERABLE",
 ("eucerin advanced repair cream", "Anyone know of a cheaper"): "JUNK",
 ("eucerin advanced repair cream", "one is better, Cerave"): "RECOVERABLE",
 ("fellow stagg kettle", "Pro"): "SELF_VARIANT",
 ("fellow stagg kettle", "Corvo"): "SELF_VARIANT",    # Fellow Corvo EKG
 ("glow recipe watermelon toner", "MCoBeauty Hydrate &"): "RECOVERABLE",
 ("helix mattress", "better, Saatva"): "RECOVERABLE",
 ("helix mattress", "tempurpedic"): "USABLE",
 ("helix mattress", "Saatva"): "USABLE",
 ("hoka clifton 9", "Bondi 9"): "SELF_VARIANT",
 ("hoka clifton 9", "nah"): "JUNK",
 ("hoka clifton 9", "Bondi 9 by a Foot Specialist"): "RECOVERABLE",
 ("hoka clifton 9", "bad"): "JUNK",
 ("kosas revealer concealer", "silicone based"): "JUNK",
 ("laneige lip sleeping mask", "original"): "SELF_VARIANT",
 ("laneige lip sleeping mask", "Milani Rose Butter Lip Mask"): "USABLE",
 ("medicube collagen mask", "real"): "JUNK",
 ("medicube collagen mask", "Biodance Mask"): "USABLE",
 ("medicube collagen mask", "there"): "JUNK",
 ("medicube collagen mask", "\u20b9200 mask"): "JUNK",
 ("olaplex no 3", "after shampoo"): "JUNK",
 ("olaplex no 3", "original"): "SELF_VARIANT",
 ("paulas choice bha exfoliant", "Korean"): "JUNK",
 ("paulas choice bha exfoliant", "La Roche Posay"): "USABLE",
 ("paulas choice bha exfoliant", "Superdrug Me+"): "USABLE",
 ("phlur missing person perfume", "Father Figure"): "SELF_VARIANT",  # Phlur's own
 ("purple mattress", "Bear"): "USABLE",
 ("purple mattress", "Nectar"): "USABLE",
 ("quip toothbrush", "Sonicare"): "USABLE",
 ("quip toothbrush", "Oral-B"): "USABLE",
 ("quip toothbrush", "brushes twice the"): "JUNK",
 ("revlon one step volumizer", "original"): "SELF_VARIANT",
 ("revlon one step volumizer", "better Dyson"): "RECOVERABLE",
 ("rhode glazing milk", "Overhyped"): "JUNK",
 ("rhode glazing milk", "Just a Splurge"): "JUNK",
 ("rhode glazing milk", "Korean skincare"): "JUNK",
 ("rhode glazing milk", "Girl I found"): "JUNK",
 ("rhode glazing milk", "Naturium Barrier Bounce"): "USABLE",
 ("rhode glazing milk", "after moisturizer"): "JUNK",
 ("rhode peptide lip treatment", "Summer Fridays Lip Butter Balm"): "RECOVERABLE",
 ("rhode peptide lip treatment", "viral peptide"): "JUNK",
 ("rhode peptide lip treatment", "Summer Fridays"): "USABLE",
 ("rhode peptide lip treatment", "bad for lips"): "JUNK",
 ("ritual multivitamin", "Wholier Plant Based Vitamin Honest"): "RECOVERABLE",
 ("rocket money app", "it Just Me"): "JUNK",
 ("rocket money app", "Monarch"): "USABLE",
 ("rocket money app", "Stick"): "JUNK",
 ("shark flexstyle", "Dyson Airwrap"): "USABLE",
 ("shark flexstyle", "Dyson Airwrap In-Depth Review and"): "RECOVERABLE",
 ("shark flexstyle", "$750 Dyson Airwrap Side-by-Side"): "RECOVERABLE",
 ("skin1004 centella ampoule", "anything else \U0001f613"): "JUNK",
 ("sol de janeiro perfume mist 62", "EDP"): "JUNK",
 ("supergoop unseen sunscreen", "Trader Joe Dupe"): "RECOVERABLE",
 ("supergoop unseen sunscreen", "chemical"): "JUNK",
 ("supergoop unseen sunscreen", "Trader Joe"): "USABLE",
 ("supergoop unseen sunscreen", "Trader Joe SPF"): "RECOVERABLE",
 ("the ordinary niacinamide serum", "fake"): "JUNK",
 ("torriden dive in serum", "Innisfree Hyaluronic Green Tea"): "USABLE",
 ("torriden dive in serum", "Isntree hyaluronic acid serum"): "USABLE",
 ("ynab budgeting app", "Actual Budget"): "USABLE",
}

led = json.loads((AN / "fullbank_competitor_ledger.json").read_text(encoding="utf-8"))
cands = [e for e in led["entries"] if e["rung"] == "candidate"]
missing = [(e["subject"], e["name"]) for e in cands
           if (e["subject"], e["name"]) not in VERDICT]
extra = [k for k in VERDICT if k not in {(e["subject"], e["name"]) for e in cands}]
assert not missing, f"unadjudicated: {missing}"
assert not extra, f"stale verdicts: {extra}"

c = Counter(VERDICT[(e["subject"], e["name"])] for e in cands)
n = len(cands)
print(f"candidate-rung entries adjudicated: {n}")
for k in ("USABLE", "RECOVERABLE", "SELF_VARIANT", "JUNK"):
    print(f"  {k:<14}{c[k]:>4}  ({c[k]/n*100:.1f}%)")

# distinct usable names after collapsing RECOVERABLE onto its parent
usable_names = defaultdict(set)
for e in cands:
    if VERDICT[(e["subject"], e["name"])] == "USABLE":
        usable_names[e["subject"]].add(e["name"])
print(f"\nsubjects with >=1 USABLE candidate: {len(usable_names)} "
      f"(of {len({e['subject'] for e in cands})} subjects reaching the candidate rung)")
print(f"distinct USABLE names: {sum(len(v) for v in usable_names.values())}")

(AN / "fullbank_candidate_adjudication.json").write_text(json.dumps({
    "method": "hand adjudication of every candidate-rung entry; reporting only, "
              "the emitter is not edited by this pass",
    "counts": dict(c), "n": n,
    "verdicts": [{"subject": s, "name": nm, "verdict": v}
                 for (s, nm), v in sorted(VERDICT.items())],
    "usable_by_subject": {k: sorted(v) for k, v in sorted(usable_names.items())},
}, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote analysis/fullbank_candidate_adjudication.json")
