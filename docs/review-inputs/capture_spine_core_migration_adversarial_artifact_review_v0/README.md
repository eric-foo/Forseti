# Capture Spine Core Migration Adversarial Artifact Review Packet v0

```yaml
retrieval_header_version: 1
artifact_role: Review input packet
scope: >
  Historical review packet index and recovery route for the Capture spine core
  migration at commit a75c337b3497d530f9b7fbfb25acb0fd230d3616.
use_when:
  - Recovering the committed inputs to PR #316's historical migration review.
  - Investigating that review's source-context hash discrepancy.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/reviews/capture_spine_core_migration_adversarial_artifact_review_prompt_v0.md
  - docs/review-outputs/adversarial-artifact-reviews/capture_spine_core_migration_adversarial_artifact_review_v0.md
```

## Retirement And Recovery — 2026-09-05

The 451 normalized snapshots and `diff_u80.patch` were retired from the current
checkout. This index, nine manifests, historical prompt and review remain.
Recover the complete committed packet from
`6d62b05aef99d541110b818157ec0ca10b85c305` when inspecting the historical inputs.
The source revisions below recover original source; they are not a recipe for
recreating the packet's normalization.

**Historical verification discrepancy:** all five recorded SHA-256 pins below
fail against the committed files at both this recovery revision and the original
packet commit `8df13cbd2ee3b655d94e315dc8cf1e258c3a9c70`. The old prompt's
`BLOCKED_SOURCE_CONTEXT` rule therefore still applies, and the review's claim
that all pins matched is not reproduced. The original pins and findings remain
verbatim as historical claims. Restoring the packet does not validate that
review or clear its source-context gate. Resolve the discrepancy or commission
a new review with freshly bound inputs before relying on that certification.

From a clone containing the recovery revision, this PowerShell command restores
into a new temporary directory, preserving committed LF bytes independently of
the host's `core.autocrlf` setting:

```powershell
$packetRecovery = Join-Path $env:TEMP ("forseti-review-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $packetRecovery | Out-Null
$packetArchive = Join-Path $packetRecovery "packet.tar"
git -c core.autocrlf=false archive --format=tar --output=$packetArchive 6d62b05aef99d541110b818157ec0ca10b85c305 docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0
if ($LASTEXITCODE -ne 0) { throw "Historical packet archive failed" }
tar -xf $packetArchive -C $packetRecovery
if ($LASTEXITCODE -ne 0) { throw "Historical packet extraction failed" }
```

Resolve the packet-relative paths below beneath `$packetRecovery`. Integrity is
equality with that revision's Git tree, not a match to the old pins: compare the
462 recovered file paths and each file's `git hash-object --no-filters` result
with `git ls-tree -r` at the recovery revision. The two snapshot manifests
enumerate 451 of those files. The retirement check recovered every member,
verified all lengths and blob identities, and rejected a corrupted patch byte;
it separately recorded all five historical pin failures. A normal Windows
archive with `core.autocrlf=true` changes text bytes and cannot supply this
committed-byte verification.

## Historical Packet Contents

This packet is generated from the migration commit, not from the later review-package commit.

Normalization note: the greppable snapshot and diff text is whitespace-normalized to satisfy repository whitespace gates. For byte-exact source, use the pinned `merge_base` and `target_ref` Git objects named below.

```text
diff_range_ref: origin/main
merge_base: 35066b1528c7b8a75476ded14461674e76fe8b51
base_snapshot_ref: 35066b1528c7b8a75476ded14461674e76fe8b51
target_ref: a75c337b3497d530f9b7fbfb25acb0fd230d3616
name_status_rows: 226
head_file_count: 226
base_file_count: 225
head_snapshot_count: 226
base_snapshot_count: 225
status_counts: A=1, M=122, R=103
```

Files:

- `diff_u80.patch` - full migration diff with 80 lines of context.
- `manifest/name_status.tsv` - Git name-status manifest with rename detection.
- `manifest/diff_stat.txt`, `manifest/numstat.tsv`, `manifest/summary.txt` - review navigation aids.
- `manifest/head_files.txt` - all target-side snapshot paths included under `head_files/`.
- `manifest/base_files.txt` - all base-side snapshot paths included under `base_files/`.
- `head_files/` - target-side snapshot text files for all added, modified, copied, or renamed-to files; original source paths are preserved with a `.snapshot.txt` suffix.
- `base_files/` - merge-base snapshot text files for all modified, deleted, copied-from, or renamed-from files; original source paths are preserved with a `.snapshot.txt` suffix.

Hash pins:

```text
diff_u80.patch sha256: 4F2DDD6E5D2AD3C9124BD9E380AD6BBDDB566C2ECAFD1D6173A4B70FB31E3EFB
manifest/name_status.tsv sha256: 087D8B18BD2AF27378188E95A2B1F8429C6E94EDE1761583A00FCE88107DF939
manifest/refs.txt sha256: 711105F253DAF841D71112086F060048D1BF6FDCB456137241732DD04F7A090B
manifest/head_snapshot_files.txt sha256: 7829ED278143AE0FA85B685C0B72C5F3966C3732D610792926B193A120FBF47E
manifest/base_snapshot_files.txt sha256: A43A6D684FDB0526C2485D8EF8D0834D72FFEE7E473C43B01A6F756128AC0E8A
```

## Historical Reviewer Use — Recover First

These original directions refer to the restored directory. They are preserved
for historical inspection; the hash discrepancy above blocks execution under
the old prompt's source-context certification.

Review the filed prompt first:

```text
docs/prompts/reviews/capture_spine_core_migration_adversarial_artifact_review_prompt_v0.md
```

Use `rg` and normal filesystem inspection inside this packet. Useful starting points:

```powershell
rg -n "social_video|capture/source_families/instagram|capture/contracts|capture/operating_model" docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0
rg -n "source_quality|cadence|missingness|satellite|web_search_capture|youtube|tiktok" docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0
rg -n "orca/product/spines/capture/" docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/head_files
```

The packet is review input only. It is not validation, approval, source-of-truth promotion, readiness, or patch authority.
