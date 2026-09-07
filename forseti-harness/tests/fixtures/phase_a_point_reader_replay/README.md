# Captured point-reader replay cases

These two cases preserve exact Summer Fridays formula and Dieux packaging
snapshot, point-payload, and response bytes captured before the saved-brief
representative-validation correction. `provenance.json` records their source
pins and the frozen consumer output hashes.

The unit test recompiles all nine points, compares the captured output bytes,
resumes through saved briefs, and challenges coherently rehashed briefs whose
selection is emptied or whose non-claim boundaries are rewritten.
It needs no provider, Collection files, or original temporary paths. These are
structural replay baselines, not semantic gold: passing them does not establish
the truth of upstream meanings, relations, or state assignments. The live
consumer contract remains in `judgment/phase_a_evidence_axis_consolidation.py`.
