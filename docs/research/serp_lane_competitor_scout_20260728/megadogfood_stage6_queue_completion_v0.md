# Megadogfood Stage 6 — queue completion v0

```yaml
artifact_role: durable Stage 6 completion record
current_as_of: 2026-07-30
authority: >
  Counts and integrity status come from the sealed operator-drive artifacts
  named below. This record owns the durable lane interpretation and future-run
  changes, not the raw packet bytes.
raw_evidence_root: C:\tmp\forseti-megadogfood-queue-completion-20260729
next_source: >
  stage6_analysis_eligibility_v1.json for per-job eligibility; the Reddit/native
  phase-2 handoff for the BR540 named-rival return.
```

## Completed capture scope

The curated queue is complete: 163 base jobs plus two dynamic Shopping
reserves have successful latest outcomes. The append-only ledger contains
148 successful fresh captures, 17 exact-query reused extractions, nine block
events, and two failed attempts. Every block and failed attempt was recovered
to a successful latest outcome.

The integrity seal freshly checked 148 packet manifests (47 lower-route,
101 persistent real-Chrome), all 592 preserved-file SHA-256 values, all 17
reused extraction paths, and query identity across all 165 successful jobs.
It found zero verification failures.

## Pruned analysis slice

Pruning is quarantine, not deletion. Raw packets and the append-only ledger
remain unchanged.

- 130 successful jobs are analysis-eligible.
- 35 successful jobs are quarantined: 31 presence-rung jobs, two under-scoped
  competitor-price jobs, and two zero-row Shopping captures.
- The eligible slice contains 3,205 observed result rows, 651 rows with a
  rendered dollar figure, and 107 captures with a rendered AI Overview.
- The surfaced fragments (`bad`, `30 levels whiter. 7. 4. Why`,
  `I brush my teeth before`, `86 Reddit-Picked`) are quarantined by the
  presence rule.
- `amazon basics price` and `CeraVe price` are separately quarantined:
  both name multi-product brands rather than the intended product class.
  `Actual Budget` is a real YNAB competitor; the capture resolved to the
  budgeting app, though future J5 grammar should say `Actual Budget app
  pricing`.

## BR540 return leg

The owner-authorized return query completed with 22 observed rows and a
rendered AI Overview. Rendered rows/snippets name Dossier Ambery Saffron
($50), Ariana Grande Cloud, Oakcha Sweven, Airplane Mode by Memoire Archives,
Montagne Le Bonbon, Untold by Armaf, Pendora Rouge by Paris Corner, Mancera
Instant Crush, and Zara Red Temptation ($35).

These are captured-surface observations, not native-community verification
or finding-grade promotions. They form the named-rival input to the next
Reddit/native pass.

## Preventive changes

Future merged queues now treat presence as cite-only, reject obvious
parser/editorial fragments before egress, and require a product scope for
competitor J5 queries. On a lower-route block, the lower transport stops; an
enabled run transitions the exact held job and remainder to one dedicated,
logged-out, operator-visible persistent Chrome tab at the same owner-set
cadence. If the persistent tab blocks, automation pauses and pings once for
manual clearance; it never interacts with the challenge. The executable seam
is `forseti-harness/runners/run_google_serp_persistent_fallback_packet.py`.

## Sealed operator-drive artifacts

- `stage6_capture_integrity_seal_v0.json` —
  `5E88F06EDF87F6B51E165A6639BC28B2BFF4FE38FFE9CD593DF3FDFF30A5D6A8`
- `stage6_analysis_eligibility_v1.json` —
  `FE9A407056B783674ECEF40EA4D761C7EF16BF54DD22457C2C08A5837C84AD50`
- `stage6_capture_completion_findings_v0.md` —
  `EE623420A25237FEA8219BAD7E0126E62A9EFC5DF7F643080CB25305FDCB19BA`

Standing non-claims: counts describe observed Google cards only, never
prevalence, volume, or share; US-parameterized capture is not proof of
physically US-local egress.
