"""Shared meaning standard for current claim authoring and interpretation."""

CLAIM_MEANING_POLICY = "supported_claim_meaning_v1"
CLAIM_MEANING_GUIDANCE = (
    "Judge source-supported meaning, not matching vocabulary. Ordinary paraphrase "
    "and context-supported entailment are valid; missing facts are not. A qualifier "
    "is material when it changes what the claim asserts, not merely how it is worded. "
    "Do not invent duration, exclusivity, intensity, or causal requirements beyond "
    "the claim and its source-supported context. Preserve actual actor, product, "
    "comparator, condition, time, uncertainty, and action-state differences. "
    "A source's own causal attribution can support a reported-experience claim "
    "without establishing objective causation; the analyst's evidentiary ceiling "
    "is not an opposing source report."
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
    "Missing a required qualifier is insufficient support, not by itself counterevidence."
)
