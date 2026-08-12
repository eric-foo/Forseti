# Success Implement Controller Boundary-Probe Diagnostic — Adversarial Artifact Review v0

```yaml
retrieval_header_version: 1
artifact_role: Adversarial artifact review report
scope: >
  Advisory-only same-vendor adversarial review of the frozen P1/E1
  controller-boundary-probe diagnostic and its three routing companions.
use_when:
  - Adjudicating whether the diagnostic accurately records the frozen experiment.
  - Deciding whether its probe, causal, integrity, or next-experiment claims need correction.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md
  - .agents/workflow-overlay/review-lanes.md
input_hashes:
  primary_target: 0542fbc2847d01415d3c9747bcd1fb3c5391bafbcaadbebe6afe42b32bdff824
  efficiency_readme: 193b7c7a069ffdfbc4b19f44d597eaab1a65dc2c40c374f9a862e663ac5e0c7f
  p4_diagnostic: ee7896785d1760ce384c1acba65c23c44405c371a140650e57ee934163aaad46
  behavioral_changelog: d8c9fb1535f160023e590314f4f67fc183d8ac8fbb361a80523695e71d85c8d3
  protocol: f3b4c475d0c48b69dd03e50785fe3a8c1838e96e4eaa63e85aa0655e298a13cd
  aggregate: aac3bbed87e5c64581b2fe01261b93f6623ec802efe0c6767f0c7b60b68a9a4f
  r1_home_adjudication: 589c0a628cc71e4d38d82967eae722814e09b91bbf7534624030e52980c4070b
  r2_home_adjudication: f8953602766ff642162ebd0f9f105184f66dc424a7f36fcf2a85323262e3cb75
  r1_e1_raw: 80512558e31d2faac035cc516fe4f6f6bcd1b5d06560e4141c70bbf34f8fd9cc
  r2_e1_raw: 95ad9024a64c5034b8445ab44f05b7877160e79fa9057ee4305794277513815c
  boundary_probe: 27cb61fa0f8e4cd83916a2a656d74fc253c6fcc154aa5661d73e11c64af4f74e
branch_or_commit: codex/si-boundary-probe-experiment at fea39cf7197c798ebb2e062e587125dea7eb6d5e; reviewed working-tree bytes were intentionally dirty
stale_if:
  - Any input hash above changes.
  - The temporary experiment packet disappears or is replaced without an identity-preserving archive.
```

## Retrieval and provenance

```yaml
reviewed_by: gpt-5.6-sol
authored_by: gpt-5.6-sol
de_correlation_bar: same_vendor_sanity
same_vendor_rationale: cross-vendor reviewer tooling was unavailable; this is an independent bounded sanity review and cannot claim discovery or no-new-seam coverage
review_lane: adversarial artifact review, advisory-only fallback
review_target: docs/workflows/efficiency/success_implement_controller_boundary_probe_diagnostic_2026_08_12_v0.md
fitness_reference: C:\tmp\forseti-boundary-probe-evidence-2026-08-12\protocol.md
output_mode: review-report
edit_boundary: only this report was writable; all reviewed sources were read-only
method_gap: >
  workflow-adversarial-artifact-review was explicitly requested but was not
  available in the session skill catalog. Repository review doctrine therefore
  limits this result to advisory-only critique, not a strict formal verdict.
```

Purpose: test whether the primary diagnostic conservatively records the frozen
P1/E1 endpoint, arithmetic, gate decisions, probe meaning, causal limits,
anonymity/integrity limits, and next experimental boundary. Use this report as
home-adjudication input only. Do not use it as study validation, approval,
readiness, mechanism proof, a patch queue, or authority to change Success
Implement.

The experiment packet at
`C:\tmp\forseti-boundary-probe-evidence-2026-08-12` was readable and hashable
during this review but remains temporary and untracked. More importantly, its
arm and judge controllers import scripts, prompts, and sources from the separate
temporary P4 packet at
`C:\tmp\forseti-goal-conservation-evidence-2026-08-12`; the current packet is
therefore not a self-contained replay or anonymity-verification archive.

```yaml
review_summary:
  status: completed
  report_path: docs/review-outputs/adversarial-artifact-reviews/success_implement_controller_boundary_probe_diagnostic_adversarial_artifact_review_v0.md
  recommendation: patch_before_acceptance
  reviewed_by: gpt-5.6-sol
  authored_by: gpt-5.6-sol
  summary: "The stop decision and all arithmetic are correct, but probe-specificity, causal, and anonymity/integrity claims outrun the frozen evidence; one minor router inconsistency remains."
  findings_count: 4
  blocking_findings:
    - AR-01: The probe does not establish the claimed Greenhouse acquisition boundary.
    - AR-02: The report promotes an unisolated internal-cause hypothesis into a finding.
    - AR-03: Evaluator anonymity and full-packet claims are not reproducible from the named packet.
  advisory_findings:
    - AR-04: The primary and changelog disagree on whether a next mechanism was selected.
  prior_findings_remediated: []
  next_action: "Home author adjudicates AR-01 through AR-04; if accepted, authorize one docs-only correction pass before relying on the diagnostic as a routing record."
```

Severity labels in this report are user-bound advisory priority labels only.
They do not create blocking, mandatory-remediation, validation, or acceptance
authority.

## Boundary framing

The load-bearing endpoint is narrow: because advancement required all eight
conditions, any failed condition must stop the study after the diagnostic and
leave current Success Implement unchanged. That endpoint does not require the
probe to be solution-neutral, causally diagnostic, or suitable as a standing
acceptance test. Those are separate interpretive claims made by the report and
must stand on their own evidence.

The principal failure modes tested before findings were:

- arithmetic or mapping drift that changes any gate truth;
- contradiction among “lexicographically better,” “two more majors,” and stop;
- a probe that is interface-specific, behaviorally overbroad, or both;
- treating `probe FAIL` as proof that acquisition was not attempted;
- inferring the actor's missing internal information from two stochastic runs;
- asserting evaluator anonymity from hashes and anonymous outputs without the
  exact evaluator inputs; and
- turning one failed opaque probe into a standing acceptance lifecycle or an
  evidence-backed next-mechanism selection.

## Independent recomputation

Counts were rebuilt from the two home-adjudication decision lists after applying
the frozen `X=E1`, `Y=P1` mappings. Resource medians were rebuilt from all four
raw-run headers, not copied from `aggregate.json`.

| Measure | P1 recomputed | E1 recomputed | Primary report | Result |
| --- | ---: | ---: | ---: | --- |
| Accepted C/M/m | `1/9/0` | `0/11/0` | same | exact match |
| Median comparison tokens | `10,580,179` | `9,111,543.5` | same | exact match |
| Median wall time | `1,088.961s` | `1,020.9435s` | same | exact match |
| E1 token change | — | `-13.881008%` | `13.88%` fewer | rounding correct |
| E1 wall change | — | `-6.246091%` | `6.25%` faster | rounding correct |

Per-repetition mappings and counts also match: r1 `P1 0/3/0`, `E1 0/4/0`;
r2 `P1 1/6/0`, `E1 0/7/0`. E1 has two more accepted majors in the pool, yet
is lexicographically better because criticals are compared first (`0 < 1`).
Those statements do not contradict the stop: advancement was a conjunction,
not a quality-only decision.

| Advancement condition | Recomputed truth |
| --- | --- |
| zero E1 criticals | `true` |
| all E1 obligations covered twice | `false` |
| no E1 broad-completion collapse twice | `false` |
| both independent final E1 probes pass | `false` |
| pooled E1 quality lexicographically better | `true` |
| no repeated new E1 major family | `true` |
| median tokens within +15% | `true` |
| median wall time within +15% | `true` |
| advance | `false` |

The only E1 major family absent from P1 in r1 was
`invalid_success_admission`; no new E1 family was absent from P1 in r2, so no
new family repeated. Both independent final-probe records are `FAIL` with
`NO_BEHAVIORALLY_DISCOVERABLE_FOUR_VENDOR_RUNNER`. The protocol-mandated
endpoint `STOP_AFTER_DIAGNOSTIC_AMPLIFIER` and unchanged-Success-Implement
decision are supported by the observed results.

## Findings

### AR-01 — The probe does not establish the claimed Greenhouse acquisition boundary

- severity: `major`
- confidence: `high`
- stable_anchor: primary target lines 59–70, “passed only if the coordinates caused an external Greenhouse acquisition attempt” and “established the probe's intended discrimination”; probe lines 37–40, 57–58, 70, 90, 106–119, and 135
- issue: The report accurately notices the probe's interface narrowness, but it still overstates the behavior that a pass demonstrates. The probe first reads every `forseti-harness/runners/*.py` source and requires all four vendor strings, then requires one exact CLI vocabulary (`--vendor`, `--company`, `--output`, and `--board-token`/`--board`). After invocation it treats the sentinel from any `socket.connect` or `socket.create_connection` call as success. It does not verify the destination, protocol, URL, request shape, or that the socket belongs to Greenhouse acquisition.
- evidence: Both E1 candidates expose `--provider`, not `--vendor`, and both final probes fail before invocation with `NO_BEHAVIORALLY_DISCOVERABLE_FOUR_VENDOR_RUNNER`. The r2 E1 raw patch independently validates a real no-payload `urllib.request.urlopen` route for Greenhouse and the other vendors, yet the probe still reports no discoverable runner. Conversely, any admitted runner that ignored the Greenhouse coordinate and opened an unrelated socket could pass. The clean-red/historical-green check therefore demonstrates compatibility with one exact discovery interface plus some socket attempt, not solution-neutral discrimination of the owner boundary.
- strongest_defense: The primary report expressly says the probe was “too narrow,” could reject alternative runner interfaces, and did not prove every valid implementation would satisfy the discovery interface.
- why_the_defense_fails: That defense covers false negatives but not the false-positive side or the source-code/filename/flag coupling. The same report still describes the pass predicate as Greenhouse acquisition and says the red/green pair established “intended discrimination,” which the executable does not test.
- impact: The advancement stop remains correct because the frozen gate observed two literal failures. What fails is the interpretation that the probe measured the intended owner boundary or was meaningfully solution-neutral. Without correction, the report can be reused as stronger evidence about executable acceptance design than the mechanism supports.
- minimum_closure_condition: The diagnostic states the probe's actual two-stage predicate—exact discovery-interface admission followed by any intercepted socket attempt—and caps the red/green result at compatibility with that predicate, without claiming Greenhouse-specific or solution-neutral boundary discrimination.
- next_authorized_action: Home adjudication of this finding; if accepted, a separately authorized docs-only correction to the diagnostic and affected companion summaries.
- advisory_direction: Preserve the correct stop result while narrowing only the probe-characterization and mechanism-validity language.

### AR-02 — The report promotes an unisolated internal-cause hypothesis into a finding

- severity: `major`
- confidence: `high`
- stable_anchor: primary target lines 130–168, especially “The missing information is task-specific executable behavior covering the owner boundary and its distinct obligations” and “The smallest materially different next experiment...”
- issue: The report moves from an observed treatment failure to a declarative internal-cause diagnosis. Two stochastic E1 runs show that this exact opaque, interface-coupled red signal did not make the conjunction pass. They do not establish what information was missing inside the actor or that task-specific transparent acceptance behavior is the causal remedy.
- evidence: The report's own evidence supplies multiple unresolved explanations: the probe feedback was only a coarse red; the discovery interface was hidden and mismatched both candidate CLIs; r2 implemented a real acquisition subset after the assigned post-implementation attempt; both P1 and E1 outcomes varied materially across repetitions; and the study exposed one case with two runs. The protocol pre-registers an advancement decision, not an estimator for internal cause. No intervention isolated transparency, obligation granularity, actionability, actor attention, or interface shape.
- strongest_defense: The report clearly labels the transparent acceptance-example proposal “untested,” restricts it to cases where such evidence already legitimately exists, and rejects standing probe ceremony. It also says E1 failed “as an implementation aid,” which is a fair result for the exact treatment.
- why_the_defense_fails: Those limits protect the proposal from becoming doctrine, but they do not cure the preceding factual sentence “The missing information is...” or the ranking “smallest materially different next experiment.” The stop result supports rejection of exact E1, not identification of the latent cause or selection among transparent acceptance, obligation state, richer feedback, or ordinary variance.
- impact: The report otherwise separates observed outcome and limits well; this sentence collapses them back together and gives the next-experiment suggestion more evidential force than the study earned.
- minimum_closure_condition: Observed effect, causal ceiling, and future hypotheses are explicitly separated; the “missing information” statement is treated as a nominated hypothesis, and no next experiment is described as selected or evidence-preferred unless a separate decision supplies that ranking.
- next_authorized_action: Home adjudication; if accepted, authorize a docs-only causal-language correction rather than a new experiment or workflow surface.
- advisory_direction: Retain the exact-E1 rejection and task-owned/no-new-ceremony safeguards; narrow only causal identification and ranking.

### AR-03 — Evaluator anonymity and “full packet” claims are not reproducible from the named packet

- severity: `major`
- confidence: `high`
- stable_anchor: primary target lines 114–115 and 176–189; current packet `controller/run_arms.py` lines 11–12, 50, and 62; `controller/run_judges.py` lines 16, 29–30, and 34–66
- issue: The report says the evaluators saw only anonymous candidates, that the evaluator packet was checked for treatment wording with none remaining, and that the “full packet” was readable at the named path. The visible outputs and scrub code are consistent with intended anonymity, but the named packet does not contain the exact evaluator contracts, case prompt, P1 source, or inherited judge/arm controller needed to reconstruct what evaluators received.
- evidence: `run_arms.py` imports `run_diagnostic.py`, the frozen P1 source, and the case dossier from `C:\tmp\forseti-goal-conservation-evidence-2026-08-12`. `run_judges.py` imports `run_diagnostic_judges.py` and points its evaluator/home contracts to that same prior temporary packet. The current blind-evaluation files use only X/Y labels, and the current scrub function removes `controller`, `probe`, `P1`, `E1`, and Success Implement wording, but prompt SHA-256 values cannot reveal or verify the prompt bytes when those bytes are absent. Both mappings also happened to be `X=E1`, `Y=P1`; the mapping files verify the labels, not blindness of the evaluator inputs.
- strongest_defense: The integrity section already says the path is temporary, not an immutable archive, and durable packet reproducibility is `NOT_PROVEN`; same-family evaluation is also disclosed. The controller code provides positive evidence of an intended scrub, and the evaluator returns themselves contain anonymous labels.
- why_the_defense_fails: The generic reproducibility caveat does not disclose that the alleged full packet is operationally dependent on a second temporary packet, nor does it narrow the categorical anonymity statements to what remains observable. Exact evaluator-input anonymity is a load-bearing study-integrity claim, not equivalent to anonymous labels in the output.
- impact: Home can rely on the observed adjudication files for counts, but cannot independently audit treatment-blinding or regenerate evaluator inputs from the named packet. The current report makes that integrity boundary look stronger and more self-contained than it is.
- minimum_closure_condition: The report records the cross-packet dependency and distinguishes three facts: anonymous labels are observed in evaluator returns; scrub logic is present in the current controller; exact dispatched evaluator inputs and their absence of treatment cues are not independently verifiable from the current packet.
- next_authorized_action: Home adjudication; if accepted, authorize a docs-only integrity-limit correction. Archiving or rebuilding the study packet is a separate decision and is not required to correct the report.
- advisory_direction: Narrow the claim to retained evidence rather than creating a new archive lifecycle by default.

### AR-04 — The primary and changelog disagree on whether a next mechanism was selected

- severity: `minor`
- confidence: `medium`
- stable_anchor: primary target lines 157–168, “The smallest materially different next experiment...”; behavioral changelog lines 131–132, “No next mechanism is selected”
- issue: The primary nominates a specific P1-versus-transparent-acceptance-example comparison as the next experiment, while the companion router says no next mechanism is selected. “Not selected as standing behavior” does not fully resolve whether an experimental mechanism was selected.
- evidence: The primary uses comparative and sequencing language (“smallest,” “next,” and “would compare”), then says the hypothesis is untested and not standing behavior. The changelog's unqualified “No next mechanism is selected” can route a future reader away from that nominated experiment.
- strongest_defense: “Selected mechanism” in the changelog can reasonably mean a deployed or standing behavior, whereas the primary only records an untested hypothesis.
- why_the_defense_fails: The documents do not state that distinction. Because both are routing artifacts, future readers should not have to infer whether “selected” means selected for experiment or selected for behavior.
- impact: This does not affect arithmetic, the stop endpoint, or current Success Implement. It creates modest routing ambiguity about the authorized next research object.
- minimum_closure_condition: The primary and changelog use one consistent posture: either an unranked candidate hypothesis with no selected next experiment, or a selected next experiment that remains untested and non-standing.
- next_authorized_action: Home adjudication and, if accepted, inclusion in the same docs-only consistency correction as any accepted major finding.
- advisory_direction: Resolve the terminology without adding a roadmap, registry, or experimental lifecycle.

## Phase 2 friction assessment

No separate standing-process finding is warranted. The primary repeatedly says
not to deploy the probe, create a skill, or install an obligation/probe
lifecycle, and it limits any acceptance example to evidence already legitimate
for the task. The README row, P4 follow-on disposition, and changelog entries
are proportionate routing updates. Their repeated result summaries add some
prose surface, but each serves a distinct directory, predecessor, or history
consumer; no evidence shows that removing one would improve the bound outcome.
AR-04 is the only material terminology drift found.

## considered_and_defended

- Candidate: “lexicographically better,” “two more majors,” and stop contradict one another. Defense held: lexicographic comparison is decided at criticals (`0 < 1`), while advancement is an eight-way conjunction; the report states both correctly.
- Candidate: pooled counts, medians, percentages, or a gate truth are wrong. Defense held: independent reconstruction exactly matched all counts and medians; reported percentages are correct rounding; four gates pass and four fail.
- Candidate: the report equates `probe FAIL` with “implementation did not attempt acquisition.” Defense held: although early summary prose can be read quickly that way, the “Overall finding” explicitly says both E1 actors built acquisition routes and failed the probe's discovery contract; r2's useful live-acquisition subset is also named.
- Candidate: the no-repeated-new-major-family gate is unsupported. Defense held: `invalid_success_admission` is new only in r1; r2 has no E1 major family absent from P1, so none repeats.
- Candidate: the stop should be softened because E1 was lexicographically better and inside resource guards. Defense held: the pre-registered conjunction makes the failed coverage, collapse, and final-probe conditions independently decisive; no weighted rescue was allowed.
- Candidate: the next-experiment paragraph installs standing ceremony. Defense held: it is explicitly untested, non-standing, and limited to acceptance evidence already legitimate for the task; the defect is causal/ranking force (AR-02), not ceremony installation.
- Candidate: evaluator provenance is falsely presented as cross-vendor. Defense held: the report explicitly calls evaluation same-family and not different-vendor delegated review; the remaining issue is exact anonymity reproducibility (AR-03).
- Candidate: the new primary lacks required retrieval metadata or the README improperly gains authority. Defense held: the primary has the required retrieval-only header and justified routing fields; the README explicitly remains a directory router rather than independent authority.

## Residual limits and non-claims

- Historical implementation worktrees and hidden contestant patches were not
  opened. The raw patch bodies included in the commissioned E1 result files
  were reviewed because those result files were required evidence.
- Candidate-reported test executions and live-provider behavior were not rerun;
  they are not needed to recompute the pre-registered endpoint.
- Patch-byte regeneration, exact evaluator prompt bytes, randomization
  implementation, and the preflight's historical-green repository state are
  not independently reproducible from the current packet alone.
- This review does not validate the study mechanism, prove solution neutrality,
  approve the diagnostic, establish readiness, claim cross-vendor discovery,
  or claim no-new-seam coverage.
- The absence of additional findings is not evidence that no other seam exists.

Read-budget audit: full-read the primary, all three companions, protocol,
aggregate, both home adjudications, both E1 raw results (including their exact
embedded patches and independent final-probe sections), probe, P4 diagnostic,
mapping files, blind-evaluation returns, and integrity preflight; targeted the
controller dependency/anonymity sections and the overlay sections controlling
artifact role, hierarchy, retrieval metadata, review, output mode, source
loading, claim support, communication, safety, and validation. Historical
implementation worktrees and hidden contestant patches were intentionally not
read under the commission boundary.

## Review-use boundary and smallest authorized next action

This is an advisory-only, read-only same-vendor sanity review. Findings and
considered-and-defended entries are decision input for home adjudication only;
they are not approval, validation, readiness, product proof, mandatory
remediation, executor-ready instructions, or authority to patch any reviewed
source.

The smallest authorized next action is for the home author to adjudicate AR-01
through AR-04 against the cited frozen evidence. If any finding is accepted,
the home author may separately authorize one bounded docs-only correction pass
over the primary and only the companion wording directly affected by that
adjudication. No rerun, new probe, archive lifecycle, Success Implement change,
or standing process is authorized by this report.
