# Semantic contract history split: dogfood and comparison — 2026-09-06

```yaml
retrieval_header_version: 1
artifact_role: Dated document-read measurement and dogfood record
scope: Semantic integration current-rule/history separation, preservation checks, and two cold lookup cases.
use_when:
  - Checking what this document split saved and which consumer was exercised.
  - Reproducing the text measurement or tracing the compatibility safeguards.
authority_boundary: retrieval_only
```

The current contract is 43.18% smaller in estimated document tokens for a
full-file read. All 120 historical entries remain intact in one sibling
changelog. This reduces routine authority-reading input; it is not a
repository-storage reduction or a measured intelligence-runtime speedup.
Current requirements remain in the
[semantic contract](../../../forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md);
version lookups use its
[history companion](../../../forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_changelog_v0.md#changelog).
Publication, required CI, and independent-review disposition belong to the lane
PR; this dated measurement does not assert their completion.

## Bound outcome and preservation

Routine current-rule readers can stop at the contract's original `## Changelog`
heading. Named historical questions follow that heading or the Phase A
workflow's seven version-reference rows and general history pointer. The
existing source-loading route makes history conditional on that question.

Both halves of the history received a read-only entry/body comparison before
editing: v0–v59 contained 62 entries; v60–v117 contained 58. The duplicated v1
and v34 numbers are correction entries and were not deduplicated. Existing
pre-changelog body text was preserved exactly apart from the v116→v117 metadata
and title correction and five explicit additions:

- Scope the targeted benchmark audit to its existing executable v2 method;
  keep v95's 2026-09-01 owner disposition dated and scoped.
- Point current selection, reader, and recovery work to its existing Phase A
  workflow owner instead of making historical receipts current procedures.
- Qualify legacy-v4 replay with v9's earlier-prompt compatibility exception.
- Preserve v38's policy-v2 `not_checked` rule and affected-v3-view regeneration.
- State the existing two-distinct-source-row convergence support floor, owned
  by the convergence `repair_attachment_instruction` branch in
  `semantic_evidence_integration.py`.

Runtime code, frozen evidence, historical version stamps, and existing entry
text were not changed. No audit, mirror run, approval checklist, or new standing
checker was added. This record and its directory-router entry are the additional
files requested by the owner's instruction to log the work.

## Measurement

Baseline: `a2474c493cf82339573ca3583c82a7557a1d9444`.
Method: UTF-8 text with Git LF newlines; words use `str.split()`; token counts
use `tiktoken 0.11.0`, encoding `o200k_base`, without message wrappers.
The tokenizer was installed only in ignored task scratch; project dependencies
were not changed. These are exact counts for that tokenizer's document input,
not native provider usage, cached/billed tokens, or measured task totals.

| Current contract | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| UTF-8 LF bytes | 266,360 | 157,802 | 108,558 (40.76%) |
| Whitespace words | 35,133 | 21,130 | 14,003 (39.86%) |
| Estimated document tokens | 54,257 | 30,830 | 23,427 (43.18%) |

The companion, including its wrapper, is 112,507 bytes / 14,422 words / 24,227
tokens. Reading both whole files costs 55,057 tokens, 800 more than the original
contract. The pair adds 3,949 tracked bytes; routing links and this record add
further text. Savings depend on excluding unneeded history from routine reads.
Already-targeted section reads do not automatically save 43.18%.

Content identity (SHA-256 of UTF-8 LF text):

- Before contract: `fe66da0c6a008b45b4258f4422998d252a37e49463aef5fda3e84a82c1e6670b`.
- After contract: `9fc8b1b29823f3bbd5775b73e80d7e1ccc4751f8b278f9b44298f696c6e280b4`.
- Companion: `b220d38184060608c5cb372100e1bac0368d955a7773e58f99d9a3b3ff630ffc`.
- Preserved payload after `## Changelog` and its newline:
  `a5ecf3dc1bb100b88e72ffcffd018da129e3bfd8ced763e5a25193232101e3ca`.

## Dogfood and falsifiers

Two separate cold, read-only helpers received operator questions without the
before state, diff, author explanation, or expected answers. This is a bounded
lookup check, not the commissioned different-vendor review or a controlled
before/after model-performance experiment.

| Case | Observed answer and route |
| --- | --- |
| Current reconciliation: temporary node growth, retained-node support, global absence claim | Correctly found zero convergence followed by convergence/retention, at least two distinct source rows, and policy-v2 `not_checked`. Used current semantic and claim-support sections; did not open history. |
| Historical reuse: early method-v4, affected v3 `none_observed`, and v86/v87 buy/try | Found the v9 exception, mandatory v38 regeneration, and v87's supersession of v86. Followed the current contract to dated entries; both v1 and v34 correction pairs remained discoverable. |

The current-reader helper read the source-loading file more broadly than needed.
The history helper's initial whole-workflow read truncated, then succeeded with
bounded reads. These are visible retrieval-efficiency residuals; neither proves
lower whole-task tokens or latency. History links land at the shared
`#changelog` heading and require a named-version search. No requested answer was
ambiguous or blocked by a dead link.

Focused preservation check: exit 0, 120 identical ordered entries, unchanged
original live body under the declared additions, 16 resolving new local links,
seven version-reference rows, and the normal-read stop instruction present.
Three in-memory perturbations failed at their intended boundaries:

| Perturbation inside the admitted document | Observed rejection |
| --- | --- |
| Change existing v9 entry to v900 | `history_payload_changed` |
| Break the existing companion anchor | `link_anchor_missing:missing-version-heading` |
| Replace mandatory regeneration with permission to reuse | `reuse_obligation_missing` |

`git diff --check` exited 0. Documentation gates and required CI are reported
with their actual exits in the lane PR. No provider calls, ingestion, extraction,
reconciliation execution, sealing, or production intelligence cycle was tested.

## Reproduction

From the repository root with tiktoken 0.11.0 available, this checks history
payload and full-file counts. If the current files have advanced, first use the
PR's frozen reviewed revision; these hashes are a dated baseline, not a standing
requirement on later legitimate changes.

```powershell
@'
from pathlib import Path
import subprocess, tiktoken
p = 'forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md'
h = p.replace('contract_v0', 'changelog_v0')
a = subprocess.check_output(['git', 'show', 'a2474c493cf82339573ca3583c82a7557a1d9444:' + p]).decode('utf-8')
b = Path(p).read_text(encoding='utf-8')
c = Path(h).read_text(encoding='utf-8')
assert a.split('## Changelog\n', 1)[1] == c.split('## Changelog\n', 1)[1]
e = tiktoken.get_encoding('o200k_base')
for label, text in [('before', a), ('after', b), ('history', c)]:
    print(label, len(text.encode('utf-8')), len(text.split()), len(e.encode(text)))
'@ | python -
```
