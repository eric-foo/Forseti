# Phase Acquisition Validator Malformed-Enum Hardening Handoff — 2026-08-07 v0

```yaml
retrieval_header_version: 1
artifact_role: Implementation handoff prompt
scope: >
  Replace the remaining unsafe enum-membership checks over operator-authored
  Phase Acquisition seal data with the validator's type-safe enum helper, and
  prove malformed list/map inputs return findings instead of crashing.
use_when:
  - Route 1.3.0 is present on main and the remaining malformed-input hardening is ready to implement.
  - Auditing run_phase_acquisition_seal_validation.py for unhashable operator-authored enum values.
authority_boundary: retrieval_only
open_next:
  - AGENTS.md
  - .agents/workflow-overlay/README.md
  - .agents/workflow-overlay/validation-gates.md
  - .agents/workflow-overlay/review-lanes.md
  - forseti-harness/runners/run_phase_acquisition_seal_validation.py
  - forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py
stale_if:
  - The Phase Acquisition validator no longer uses _is_enum_value for type-safe scalar enum admission.
  - A later change replaces the seal validator or its enum representation.
  - Route 1.3.0 is absent from the receiver's current main branch.
```

## Prompt Preflight

```yaml
output_mode: chat-only
edit_permission: implementation-authorized
targets:
  - forseti-harness/runners/run_phase_acquisition_seal_validation.py
  - forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py
branch: fresh receiver-owned branch or worktree from current main after the Phase A route 1.3.0 change lands
dirty_state_allowance: clean at intake; only the two named targets may change
input_prompt_source: docs/prompts/handoffs/phase_acquisition_validator_malformed_enum_hardening_handoff_20260807_v0.md
output_artifact: none; patch the named code/tests and return the observed validation in chat and the lane PR
preflight_defaults: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md v0 - constants bound; deltas stated inline.
```

## Bound Outcome

One complete mechanical sweep of
`run_phase_acquisition_seal_validation.py` makes every enum membership check
whose candidate value comes from operator-authored JSON/YAML safe against
unhashable values such as a list or mapping. A malformed value must produce the
site's existing typed finding and let validation continue; it must never raise
`TypeError` or create a permissive success path.

This is validation hardening only. It does not change the Phase A route,
schemas, allowed enum values, finding names, evidence bars, pass/fail meaning,
or current/historical version obligations.

## Receiver Task

1. Fresh-read both targets and locate every remaining `value in SET`,
   `value not in SET`, or equivalent set/dict-membership expression where
   `value` ultimately comes from the submitted seal or a referenced
   operator-authored artifact.
2. Classify before editing:
   - **In scope:** scalar enum/state/role/kind/posture/status values whose
     malformed list/map shape could reach a hash lookup.
   - **Out of scope:** membership over validator-owned IDs already normalized
     into a string set, ordinary list containment that is safe for unhashable
     values, recursive key inspection, numeric/range validation, and any check
     whose candidate is locally constructed and proven hashable.
3. Replace each in-scope expression with `_is_enum_value(value, allowed)` or a
   semantically identical type-safe branch. Preserve the existing finding code,
   branch order, valid-input behavior, and downstream checks.
4. Add parameterized regression coverage that injects both a list and a mapping
   at every changed enum site (group sites only when the same test clearly names
   every mutated path and expected finding). Each case must assert:
   - validation returns rather than raising;
   - the existing invalid-value finding is present;
   - no malformed value receives completion/pass credit.
5. Search again after the patch and account for every remaining direct set/dict
   membership involving operator-authored values: changed, proven safe, or
   explicitly out of scope with one-line reasoning in the PR body. Do not add a
   permanent registry or runtime receipt for this accounting.

## Hard Boundaries

- Do not add new route or schema versions.
- Do not rename findings or collapse specific findings into a generic error.
- Do not catch broad exceptions around validation.
- Do not coerce lists/maps to strings, tuples, booleans, or defaults.
- Do not turn malformed input into a warning when it currently blocks.
- Do not refactor unrelated validator logic, fixtures, artifact hashing, or
  evidence doctrine.
- Do not edit Phase A authority/playbook/prompt documentation in this lane.
- Preserve historical-route version symmetry.

## Validation

Run in this order and stop the broad step if the focused test fails:

```powershell
python -m pytest forseti-harness/tests/unit/test_phase_acquisition_seal_validation.py -q
python -m compileall -q forseti-harness/runners/run_phase_acquisition_seal_validation.py
git diff --check
python .agents/hooks/check_review_routing.py --strict --base origin/main
```

If the repository's current validation-gate authority requires an additional
code-root check, run it and report the exact command and observed result. Report
every required check as pass, fail, blocked, or not run. A test process that
crashes is a failure, not a finding.

## Completion And Lifecycle

Fresh-read the two changed files, show the final targeted unsafe-membership
search, and report the exact changed-site count plus test count from observed
output. If validation is clean, follow the receiver's ordinary Forseti branch
PR flow from `AGENTS.md`; do not merge another actor's PR and do not bypass a
required code-review route. Return the commit/PR identity only after a fresh
read proves it. The lifecycle hard stop in the preflight defaults applies to
every action not explicitly granted here.

## Plain-Language Summary

The validator already knows how to reject a bad enum value safely. Use that
safe check everywhere user-authored seal data can reach an enum lookup, then
prove that both `[]` and `{}` yield normal findings instead of crashing the
whole validation run.
