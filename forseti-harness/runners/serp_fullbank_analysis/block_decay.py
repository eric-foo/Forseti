r"""Seal the block-decay series (F2b/F3 evidence) from orchestrator.log.

Every block -> next-attempt gap with its outcome, minus the three
2026-07-29 01:48-01:51 rows voided by the ledger's RETRY_CORRECTION
(retry helper re-read archived blocked packets in 0s without contacting
Google; no probe occurred). Writes analysis/fullbank_block_decay.json.
Store path operator-drive-pinned like the rest of this directory.
"""
import json
import re
import sys
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")
VOID_WINDOW = (datetime.datetime(2026, 7, 29, 1, 48),
               datetime.datetime(2026, 7, 29, 1, 52))

rx = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?:RETRY )?"
                r"(j\d+) (ok|blocked)")
rows = []
for line in (ROOT / "orchestrator.log").read_text(encoding="utf-8").splitlines():
    m = rx.match(line)
    if not m:
        continue
    t = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    rows.append((t, m.group(2), m.group(3)))

series = []
for i, (t, j, o) in enumerate(rows):
    if o != "blocked" or i + 1 >= len(rows):
        continue
    if VOID_WINDOW[0] <= t <= VOID_WINDOW[1]:
        continue                       # RETRY_CORRECTION-voided fabrications
    nt, nj, no = rows[i + 1]
    series.append({"blocked_at": t.strftime("%Y-%m-%d %H:%M:%S"),
                   "job": j, "next_job": nj, "next_outcome": no,
                   "gap_minutes": round((nt - t).total_seconds() / 60, 1)})

cleared = sorted(s["gap_minutes"] for s in series if s["next_outcome"] == "ok")
failed = sorted(s["gap_minutes"] for s in series if s["next_outcome"] == "blocked")
out = {
    "artifact": "fullbank_block_decay",
    "derivation": "block_decay.py over orchestrator.log; voided retry rows "
                  "excluded per run_ledger RETRY_CORRECTION",
    "series": series,
    "gaps_cleared_minutes": cleared,
    "gaps_failed_minutes": failed,
    "reading": "decay is stochastic, not a deterministic bracket: gaps of "
               "12.5 and 14.7 min each cleared once the same morning an "
               "81.8-min wait failed; 77.5 failed while 83.4, 110.8, and "
               "207.6 cleared. Elapsed idle alone does not separate the "
               "outcomes observed so far.",
    "non_claims": ["n is small and every gap is confounded with run/rung "
                   "history; this series bounds nothing, it only refutes "
                   "deterministic brackets"],
}
(ROOT / "analysis" / "fullbank_block_decay.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"cleared gaps: {cleared}")
print(f"failed gaps : {failed}")
print("wrote analysis/fullbank_block_decay.json")
