# Turn 08 Workflow Bedrock Maximization

```yaml
retrieval_header_version: 1
artifact_role: Workflow strategy record
scope: Turn 08 docs-first sequencing strategy for deep-thinking, product planning, and feature planning workflow methods.
use_when:
  - Reconstructing early Orca workflow-method sequencing decisions.
  - Checking why product planning precedes feature planning for Orca work.
open_next:
  - .agents/workflow-overlay/source-loading.md
  - .agents/workflow-overlay/skill-adoption.md
authority_boundary: retrieval_only
```

- Status: PROPOSED_LOCK
- Superseded in part (2026-07-25): the standing "wrap every high-stakes
  decision in deep-thinking" posture in this record is not live doctrine.
  Deep-thinking runs on explicit invocation only, per the
  `workflow-deep-thinking` scope in `.agents/workflow-overlay/skill-adoption.md`
  and the overlay Behavioral Admission; the Batch 0 benchmark
  (`docs/workflows/process_improvement_batch0/deep_thinking_benchmark_v0.md`)
  closed with no standing deep-think obligation.
- Date: 2026-05-13
- Scope: docs-first workflow strategy for maximizing the first three Orca workflow methods
- Implementation authorized this turn: no

## Source Basis

Orca authority loaded:

- `AGENTS.md`
- `.agents/workflow-overlay/README.md`
- `.agents/workflow-overlay/project-authority.md`
- `.agents/workflow-overlay/source-of-truth.md`
- `.agents/workflow-overlay/artifact-folders.md`
- `.agents/workflow-overlay/validation-gates.md`
- `.agents/workflow-overlay/review-lanes.md`
- `.agents/workflow-overlay/safety-rules.md`
- `.agents/workflow-overlay/skill-adoption.md`
- `docs/decisions/turn_08_product_thesis_v0.md`

External workflow source inspected read-only:

- `C:\Users\vmon7\Desktop\projects\agent-workflow\README.md`
- `C:\Users\vmon7\Desktop\projects\agent-workflow\AGENTS.md`
- `C:\Users\vmon7\Desktop\projects\agent-workflow\skills\candidates\promote-now\deep-thinking\SKILL.md`
- `C:\Users\vmon7\Desktop\projects\agent-workflow\governance\charter-references\snapshots\orca_workflow_kernel_skill_inventory_matrix.md`
- `C:\Users\vmon7\Desktop\projects\agent-workflow\governance\charter-references\snapshots\orca_workflow_kernel_migration_charter.md`
- `C:\Users\vmon7\Desktop\projects\agent-workflow\governance\charter-references\snapshots\orca_workflow_kernel_layer_contract.md`

Source hashes:

| Source | SHA256 |
| --- | --- |
| `docs/decisions/turn_08_product_thesis_v0.md` | `5899FC4D6B11CC5480A6CB355C41CFF6589DC71B76E62591618347ACDBD86B37` |
| `agent-workflow/README.md` | `AE5296F3331C1E7360A756E08E794BDC206A39DAE47FC79115E2EAB5AD60FE63` |
| `agent-workflow/AGENTS.md` | `52DF84081EC17B1B8C334CFE67EFE936A8D51E333B9537ED1D7B321F1E642158` |
| `agent-workflow/skills/candidates/promote-now/deep-thinking/SKILL.md` | `6CADFCA02A6A48CF462BC69C10203168E17A94BF423FA053F6CDC8657C9F001C` |
| `agent-workflow/governance/charter-references/snapshots/orca_workflow_kernel_skill_inventory_matrix.md` | `EAD9B48C29A44DB435474A3E3BE965BE28E974F36206DA991D047D098A982FF4` |
| `agent-workflow/governance/charter-references/snapshots/orca_workflow_kernel_migration_charter.md` | `EF8C7947FD77D35F7E368AE37CF18E91387CB808C4E26BD6359C93ED5AA019A5` |
| `agent-workflow/governance/charter-references/snapshots/orca_workflow_kernel_layer_contract.md` | `8C258610E493A0C2FC7B899B48805B88BF316B61402E5AB1D2714139B3EEBD14` |

Important source constraint:

`agent-workflow` currently exposes `workflow-deep-thinking` as a canonical candidate. `product-ultraplan` and `feature-ultraplan` are described in migration records as future shadow-name candidates, but their reusable source files are not yet present as accepted canonical skill files in `agent-workflow`. This note therefore maximizes their intended mechanics and sequencing without installing, copying, promoting, or treating any `jb` repo-local skill as Orca authority.

## Bedrock Thesis

These three methods should be treated as one decision system:

- `workflow-deep-thinking`: prevents anchoring, forces option comparison, names assumptions, and verifies the recommendation.
- Future `workflow-product-ultraplan`: turns Orca's thesis into explicit product bets, evidence standards, kill criteria, and allocation questions before any feature plan exists.
- Future `workflow-feature-ultraplan`: translates a selected product bet into capability plans, validation units, red-team checks, and bloat control without rushing into implementation.

For Orca, the maximum value comes from using them in sequence:

1. Deep-thinking frames the real allocation decision.
2. Product-ultraplan decides which product bet deserves evidence.
3. Deep-thinking checks whether the product bet is overfit, under-evidenced, or missing a better hybrid.
4. Feature-ultraplan plans the smallest evidence-producing capability set for the chosen bet.
5. Deep-thinking verifies the final plan and records assumptions that would change it.

## Maximizing `workflow-deep-thinking`

Use it as the reasoning wrapper around every high-stakes Orca decision, especially when the phrase "frontier OSINT" risks becoming an assumed solution instead of a judged capability.

Best use:

- define the actual decision before planning sources, workflows, or systems;
- compare plausible options, including options not proposed in the prompt;
- downgrade or eliminate options only with explicit reasons;
- preserve hybrid options when the best answer is a composition;
- name missing evidence, hidden assumptions, failure modes, and what would change the recommendation;
- end with a concrete recommendation.

For Orca, the default deep-thinking criteria should be:

- allocation decision value;
- public-signal evidence quality;
- source provenance and timestamp strength;
- risk of false positives, astroturfing, repetition, or hype;
- actionability for product, positioning, pricing, growth, or competitive response;
- compliance with Orca's market-level, non-dossier product boundary;
- suitability for Client 0 validation through `jb`.

## Maximizing Future `workflow-product-ultraplan`

Use it before any feature planning. Its job is to prevent product ambiguity from turning into premature OSINT tooling, implementation roadmaps, or data collection breadth.

For Orca, a product-ultraplan run should answer:

- What allocation decision are we trying to improve?
- Who makes that decision, and what budget or roadmap consequence follows?
- What outside-in signal would change the decision?
- What evidence would make the signal trustworthy enough to act on?
- What public-signal categories matter for this decision?
- What signal-quality threats could mislead us?
- What recommendation verbs are allowed: build, test, reposition, defend, monitor, ignore, delay, or kill?
- What kill criteria prevent Orca from preserving a weak thesis?

The output should be a decision memo plan, not a feature roadmap. It should include:

- product bet;
- alternatives considered;
- evidence standard;
- public-signal relevance lens;
- confidence and uncertainty;
- decision owner and decision consequence;
- kill, delay, or test criteria;
- handoff boundary to feature planning.

Orca-specific adaptation:

Replace generic PMF language with allocation-risk language unless an accepted Orca source explicitly needs PMF terminology. Orca's first proof is not external willingness to pay; Client 0 proves method quality, data spine, signal-quality judgment, and decision-memo usefulness.

## Maximizing Future `workflow-feature-ultraplan`

Use it only after product-ultraplan identifies a product bet worth planning. Its job is to turn the selected bet into the smallest capability set that can produce decision-grade evidence.

For Orca, feature-ultraplan should plan capabilities as evidence instruments:

- source capture proves provenance and timestamp integrity;
- excerpt capture proves claims can be audited;
- deduplication prevents repeated language from looking like independent demand;
- clustering reveals market patterns without flattening source context;
- source-quality scoring separates credible market pull from low-quality noise;
- artificial-amplification flags prevent overreaction to seeded or suspicious narratives;
- evidence appendices make recommendations inspectable;
- decision memos turn signal patterns into allocation choices;
- outcome feedback tests whether Orca's judgments were directionally useful.

Feature planning should be mode-based:

- Lean: one narrow decision question, one or two source families, lightweight evidence memo, explicit unknowns.
- Great: multi-source evidence, confidence scoring, red-team pass, decision memo with alternatives and kill criteria.
- Extreme: frontier OSINT depth, adversarial source-quality review, suspicious-amplification analysis, outcome-tracking plan, and repeatable evidence packet.

Until implementation is authorized, feature-ultraplan output must stay as documentation: capability boundaries, evidence requirements, validation plan, risks, and bloat queue.

## Combined Operating Loop

Use this loop for every major Orca planning move:

1. Overlay preflight: load Orca authority and fail visibly on missing required sources.
2. Deep-thinking frame: define the real decision and criteria.
3. Product-ultraplan: choose or reject the product bet before planning capabilities.
4. Deep-thinking verification: check alternatives, assumptions, and weak evidence.
5. Feature-ultraplan: plan the smallest evidence-producing capability set.
6. Red-team and bloat queue: remove impressive but non-decision-critical scope.
7. Decision memo: record recommendation, evidence standard, confidence, next test, and kill criteria.
8. Outcome memory: after the decision plays out, record what Orca got right or wrong.

## First Orca Use Cases

The first three runs should stay docs-first:

1. Product-ultraplan Client 0: decide the strongest `jb` finance-career avatar, pain wedge, copy angle, pricing/package, and workflow bet to investigate through public signals.
2. Product-ultraplan OSINT foundation: decide which public-signal source families and quality controls matter most for Orca's value proposition.
3. Feature-ultraplan evidence spine: plan the docs-only capability map for provenance, excerpts, clustering, deduplication, confidence scoring, artificial-amplification flags, and decision memo output.

Each run should be wrapped by deep-thinking before and after the ultraplan pass.

## Do Not Do Yet

- Do not install, rename, copy, shadow, or promote skills.
- Do not create implementation folders, packages, tests, runtimes, scrapers, or automation.
- Do not import `jb` lifecycle rules, product policy, paths, or validation habits as Orca authority.
- Do not let "technical OSINT frontier" become a substitute for a precise allocation decision.
- Do not build broad source collection before deciding which decision the evidence must improve.

## Next Recommended Artifact

Create a docs-first prompt artifact for the first Orca `product-ultraplan` run:

`docs/prompts/product_ultraplan_client0_public_pull_v0.md`

That prompt should ask for a decision memo plan for Client 0 and should require:

- Orca thesis source;
- target allocation decision;
- public-signal source map;
- evidence-quality criteria;
- signal-quality threats;
- recommendation verbs;
- kill criteria;
- handoff boundary to feature-ultraplan.
