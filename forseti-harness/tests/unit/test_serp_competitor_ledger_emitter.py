"""Pinned-fixture regression check for competitor_ledger.py.

Runs the emitter on both stores and asserts the real names it must find
and the junk it must not. Presence-based (robust to store growth).
Run after ANY emitter edit; a silent regression (like the NYX drop
caught 2026-07-28) fails loudly here.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

BIN = Path(__file__).parent
T28 = Path(r"C:\tmp\forseti-tower28-scout-20260727")
FAILS = []


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


def run(args, out):
    subprocess.run([sys.executable, "-B", str(BIN / "competitor_ledger.py"),
                    *args, "--output", str(out)], check=True,
                   capture_output=True)
    return json.loads(out.read_text(encoding="utf-8"))


def entry(d, subject, name_part, typ):
    return any(e["subject"] == subject and typ == e["type"]
               and name_part.lower() in e["name"].lower()
               for e in d["entries"])


with tempfile.TemporaryDirectory() as td:
    t28 = run(["--extractions", str(T28 / "extracted_v2"),
               "--subject", "tower 28 swipe concealer",
               "--subject", "tower 28",
               "--subject", "tower 28 sos spray"], Path(td) / "t28.json")
    mega = run([], Path(td) / "mega.json")

# Tower 28 store: real names, correct types/directions
check("t28: NYX is dupe_association of swipe concealer (direction)",
      entry(t28, "tower 28 swipe concealer", "nyx", "dupe_association"))
check("t28: Hourglass is anchor_up",
      entry(t28, "tower 28 swipe concealer", "hourglass", "anchor_up"))
check("t28: Saie found as rival (unprompted entrant)",
      entry(t28, "tower 28 swipe concealer", "saie", "rival"))
check("t28: Haus Labs found via or-pattern",
      entry(t28, "tower 28 swipe concealer", "haus labs", "rival"))
check("t28: outlets routed to mediators, not ledger",
      not any("you beauty" in e["name"].lower() for e in t28["entries"])
      and any("You Beauty" in m for m in t28["mediators"]))
check("t28: use-context junk rejected (no 'acne prone skin' entries)",
      not any("prone skin" in e["name"].lower() for e in t28["entries"]))

# Megadogfood store: real candidates survive, junk stays dead
check("mega: Summer Fridays Lip Butter Balm rival of Rhode",
      entry(mega, "rhode peptide lip treatment", "summer fridays", "rival"))
check("mega: Amazon Basics rival of CeraVe at candidate rung",
      any(e["subject"] == "cerave moisturizing cream"
          and "amazon basics" in e["name"].lower()
          and e["rung"] == "candidate" for e in mega["entries"]))
check("mega: Vanicream found (seeded vs probe still harvests)",
      entry(mega, "cerave moisturizing cream", "vanicream", "rival"))
check("mega: imperative junk dead ('Recommend', 'Find Your Perfect')",
      not any(e["name"].lower().startswith(("recommend", "find your"))
              for e in mega["entries"]))
check("mega: bare context word 'body' not an entry name",
      not any(e["name"].lower() == "body" for e in mega["entries"]))
check("mega: no question-word fragment names",
      not any(e["name"].lower().startswith(("what ", "which ", "how "))
              for e in mega["entries"]))

print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nALL PASS")
sys.exit(1 if FAILS else 0)
