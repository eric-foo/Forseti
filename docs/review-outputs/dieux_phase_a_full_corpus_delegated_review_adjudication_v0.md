# Dieux Phase A full-corpus delegated review adjudication v0

```yaml
retrieval_header_version: 1
artifact_role: delegated_review_adjudication
scope: >
  Durable review and home-adjudication record for the Dieux Phase A full-corpus
  consolidation work landed by PR #1530.
use_when:
  - Checking the independent-review disposition behind the Dieux Phase A consolidation machinery.
  - Interpreting the mixed reader-method disclosure in the final Dieux completion receipt.
stale_if:
  - A later review supersedes these findings or the saved Dieux completion snapshot is regenerated.
authority_boundary: retrieval_only
```

```yaml
reviewed_by: Claude (Anthropic), Opus 5
authored_by: OpenAI/Codex GPT-5
reviewed_head_sha: f42c50ecd097b546ea4d606487667e773303e4fe
final_pr_head_sha: 8d315f1f1dcdc838f22153a0e6e333978cba220f
merged_main_sha: 85b6108ddf41fa3f18e024277fe4303ef632acbf
pr: 1530
review_mode: different-vendor findings-only review with home adjudication
review_return_sha256: 9651eb574cda25e1d9de9864db889878adb3f55ffe46071c73d320ba1e5b5d61
home_adjudication: complete
review_use_boundary: >
  Findings are decision input only and are not approval, validation, mandatory
  remediation, or patch authority.
```

## Outcome

The reviewer returned `FINDINGS_ONLY_NO_IN_SCOPE_PATCH`. Two findings were
accepted. Eleven other candidate findings were rejected after the reviewer
attempted to reproduce them. Home adjudication changed no frozen evidence and
made no Deliver judgment.

## Accepted finding F-01: locked runtime dependencies

The harness declared `jsonschema` but its lock file had not been refreshed, and
`provider_attempts.py` directly imported `referencing` without declaring it as a
direct dependency. The reviewer reproduced both consequences: `uv lock --check`
failed and the lock-managed environment could not import the reader runner.

The final PR head declared `referencing>=0.35,<1` and refreshed `uv.lock`.
Observed validation at that head included:

- `uv lock --check`: pass;
- locked-environment imports of `jsonschema`, `referencing`, and
  `provider_attempts`: pass;
- locked-environment launch of `run_semantic_evidence_integration.py --help`:
  pass;
- 397 focused tests: pass;
- ten pre-push gates: pass; and
- PR route and harness CI checks: pass.

## Accepted finding F-02: mixed reader methods

The saved completion index combined valid outputs generated under three reader
method revisions. The original wording could be read as uniform-current-method
coverage, which the artifacts did not prove.

The immutable corrected receipt is
`C:\tmp\forseti-phase-a-dieux-consolidation-completion-20260904-v3` on the
authoring host. It records this exact accepted-placement distribution:

| Reader method SHA-256 | Axes | Accepted placements | Current method |
| --- | ---: | ---: | --- |
| `54b0ab200b3a33be56a7ac53bdce9a9d05d53859bc4cc6d6b90f968f4e636dea` | 4 | 124 | no |
| `4dc66ada934eeff94f05d5dba8c4cc0fc4c716293f38d14fb116ee5edda3de62` | 3 | 118 | no |
| `cef49f92f070efbe903eb4e20fc7b0a18ff1ca1bc00b57297a8c28abf5e6d91e` | 1 | 45 | yes |

All eight saved axis outputs passed their snapshot-bound consumer validators.
Uniform current-reader generation remains `NOT_PROVEN`: 242 accepted placements
across seven axes retain their valid older-method outputs. They were not
regenerated solely for version uniformity because no material defect had been
observed in those axes.

Corrected proof hashes:

- `completion-index.json`:
  `526285d320bdb07e03ebe639d3e84a35d7511d582b1b167a2089b0bf8f59d6df`;
- `completion-receipt.json`:
  `07d8710c268747c16df9ac28edbeb995b67863604cb4cbc7cb0d6cee95223557`;
- `sha256-manifest.json`:
  `c0135519a64b33d4ed4fe63cb8a1c1c7f1d8fedc8fadd3cc5602ae0b5e9953fc`.

## Publication note

PR #1530 was squash-merged after its branch checks passed. The first `main` CI
run stopped at the review-routing gate because the custom squash message omitted
the branch commit's `review_routing_status` line and no review output was yet
stored in the repository. The code and test steps were not reached in that run.
This record supplies the missing durable review provenance; it does not recast
that failed run as a passing run.

## Non-claims

- Mechanical validation does not prove semantic truth or reader quality.
- The older-method outputs are not presented as current-method outputs.
- Accepted placements are not unique-customer or prevalence counts.
- This review contains no Deliver recommendation.
- This record does not retroactively change frozen evidence or model responses.
