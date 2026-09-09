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

# The original constants above are the immutable supported_claim_meaning_v1
# policy. New authoring selects this policy explicitly; saved v1 attempts replay.
CONTEXTUAL_CLAIM_MEANING_POLICY = "contextual_claim_meaning_v2"
CONTEXTUAL_CLAIM_MEANING_GUIDANCE = (
    "Interpret what the source communicates in its supplied context, not isolated "
    "words or grammatical tense. Ordinary paraphrase, implied references, and "
    "experience-based advice can express a customer-reported benefit without a "
    "formal first-person event narrative. A customer's 'this will help you' within "
    "an account of use can be an endorsement informed by experience; 'I hope it "
    "will help; I have not tried it' is anticipation. Decide from the whole account, "
    "not the word 'will'. Preserve genuine uncertainty and distinguish reported "
    "experience, expectations, and objective proof. Source role affects what "
    "evidentiary credit a report can carry, not whether its words have meaning; "
    "ordinary customer testimony needs no scientific proof to count as testimony, "
    "but neither public authorship nor confidence establishes objective causation. "
    "Keep material actor, product, comparator, condition, time, and action differences. "
    "Do not invent a duration, intensity, role, purpose, or other requirement absent "
    "from the claim. Later events do not erase an earlier reported state unless "
    "the claim requires it to persist. Read available original source wording as "
    "the authority for interpretation; a normalized summary is an aid, not a "
    "substitute for that wording. Context may clarify the source's assertion but "
    "must not donate another actor's experience or an unrelated clause's benefit."
)
CONTEXTUAL_CLAIM_RELATION_GUIDANCE = (
    "Support is relevant evidence for the bounded finding; counter is relevant "
    "contrary experience, behavior, or judgment, not simply failure to satisfy "
    "the positive description. A never-tried plan is context for a regular-use "
    "finding and may support an interest finding; it is not contrary use "
    "experience. A tried-and-abandoned routine can be counter to current regular "
    "use even without negative sentiment. An experienced lack of recovery can "
    "counter a recovery finding; do not excuse it merely because it says 'yet' "
    "or invent a minimum trial duration. Judge whether the source supplies a "
    "meaningful contrast for this particular finding, rather than imposing a "
    "universal requirement that every source must have used the product. Relevant "
    "material that establishes neither side is adjacent; out-of-scope material "
    "is exclude. Do not turn interest into observed use or suppress genuine "
    "negative evidence. Relation strength must follow the source's meaning."
)
CONTEXTUAL_CLAIM_FORMATION_GUIDANCE = (
    CONTEXTUAL_CLAIM_MEANING_GUIDANCE + " When forming a claim, choose an informative "
    "shared assertion each supporting source communicates in context. Do not "
    "manufacture a stronger status or a more specific event merely to make the "
    "claim precise. Preserve source-specific details in their lineage. "
    + CONTEXTUAL_CLAIM_RELATION_GUIDANCE
)
CONTEXTUAL_CLAIM_INTERPRETATION_GUIDANCE = (
    CONTEXTUAL_CLAIM_MEANING_GUIDANCE
    + " The bounded finding is fixed; do not broaden it to admit a row. "
    + CONTEXTUAL_CLAIM_RELATION_GUIDANCE
)
CONTEXTUAL_CLAIM_CONFIRMATION_CRITERION = (
    "State the point's single meaning in point_scope_reason, including its "
    "material action/object and time. Derive scope from the finding, not from "
    "candidate labels or invented eligibility thresholds. Apply the contextual "
    "relation guidance to each source_body together with that row's normalized "
    "meanings and bound parent context. Do not manufacture an opposing class by "
    "negating the support criterion: no relevant experience is different from "
    "a contrary experience, and attitudes are judged as attitudes."
)
CONTEXTUAL_CLAIM_REF_INSTRUCTION = (
    "For every row, return relation_semantic_unit_refs as the smallest nonempty "
    "subset of its supplied primary_semantic_unit_ref and "
    "same_evidence_companion_meanings_with_refs whose source-supported meaning "
    "warrants the relation. Original source_body may clarify these meanings, "
    "not supply foreign refs or license unrelated claims. When a normalized "
    "assertion overstates its original source, do not credit the overstatement; "
    "state the source-grounded limitation in reason_code without rewriting "
    "the saved meaning. Missing source_body is unavailable context, not evidence "
    "of absence."
)
