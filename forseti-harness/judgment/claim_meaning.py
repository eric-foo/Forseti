"""Shared meaning standard for current claim authoring and interpretation."""

CLAIM_MEANING_POLICY = "supported_claim_meaning_v1"
CLAIM_MEANING_GUIDANCE = (
    "Judge source-supported meaning, not matching vocabulary. Ordinary paraphrase "
    "and context-supported entailment are valid; missing facts are not. A qualifier "
    "is material when it changes what the claim asserts, not merely how it is worded. "
    "Do not invent a requirement the claim does not state; duration, exclusivity, "
    "intensity, role, and causation are common examples, not the whole set. "
    "Preserve actual actor, product, comparator, condition, time, uncertainty, "
    "and action-state differences. "
    "Distinguish source facts from the analyst's evidentiary limits: 'does not "
    "establish X' does not mean 'X did not happen' or require the source to avoid "
    "asserting X. Judge an assertion at its stated time; a later event does not "
    "erase an earlier report unless the claim requires that state to persist. "
    "A source's own causal attribution can support a reported-experience claim "
    "without establishing objective causation."
)
CLAIM_FORMATION_GUIDANCE = (
    CLAIM_MEANING_GUIDANCE
    + " When forming a claim, choose an informative shared assertion that each "
    "supporting source establishes. Do not add an analyst's stronger status label "
    "or threshold just to make the claim sound precise. Keep source-specific "
    "detail in its lineage rather than requiring every source to repeat it."
)
CLAIM_INTERPRETATION_GUIDANCE = (
    CLAIM_MEANING_GUIDANCE
    + " Here the bounded claim is already fixed: do not broaden it to admit a row. "
    "Support establishes that claim, counter establishes a materially incompatible "
    "report of the same predicate, and adjacent is relevant but establishes neither. "
    "Missing a required qualifier is insufficient support, not by itself counterevidence. "
    "A row reporting that the claim's own precondition never arose for its own "
    "speaker is likewise insufficient support rather than counter; counter needs an "
    "incompatible outcome for the same predicate, not the absence of the occasion."
)
CLAIM_CONFIRMATION_CRITERION = (
    "First state the point's single meaning criterion in point_scope_reason, "
    "including its action/object and temporal state and separating any analyst "
    "evidentiary ceiling. Draw that criterion only from what the bounded point "
    "itself states; do not narrow it with a role, purpose, or condition the point "
    "leaves unstated. Apply that same criterion to every row; do not redefine "
    "it to fit a candidate."
)
CLAIM_REF_SCOPE_NOTE = (
    " This ref rule governs which refs you cite, not how you read them: it does "
    "not override the meaning standard above or forbid reading a row's own "
    "source-supported meaning in its supplied context."
)
