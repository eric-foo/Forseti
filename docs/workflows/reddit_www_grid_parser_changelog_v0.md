# Reddit WWW Grid Parser Changelog v0

```yaml
retrieval_header_version: 1
artifact_role: Parser-version changelog
scope: Human-readable meaning and evidence for Reddit WWW grid parser identifiers stored in capture packets.
use_when:
  - Interpreting a Reddit WWW grid packet's parser_version.
  - Changing WWW_GRID_PROJECTION_PARSER_VERSION or its parsing behavior.
authority_boundary: retrieval_only
open_next:
  - forseti-harness/capture_spine/reddit_subreddit_grid/www_grid_projection.py
  - forseti-harness/tests/unit/test_www_grid_projection.py
stale_if:
  - WWW_GRID_PROJECTION_PARSER_VERSION changes without a matching entry here.
  - A cited packet, test, or pull request no longer supports the stated delta.
```

The current write-time identifier and behavior are owned by
`www_grid_projection.py`; this changelog explains version history and does not
override code or packet evidence.

The human name is **Reddit WWW Grid Parser vN**. Capture packets use the
unambiguous stored identifier `reddit-www-grid-parser-vN`. The earlier `www-7`
identifier is retained only as a legacy label on the transient v7 canary packet;
stored packet provenance is never rewritten to match newer naming.

## v8 — current

Stored identifier: `reddit-www-grid-parser-v8`

- `+` Excludes promoted elements even when they carry a canonical-looking Reddit
  thread permalink.
- `+` Emits one semantic row per canonical organic thread URL.
- `+` Counts organic post elements independently from row emission, so malformed
  rows remain visible to the projection-anomaly guard.
- `+` Self-heals at the next post element after a missing end tag instead of
  silently swallowing all later posts.
- `-` Removes v7's nested-post suppression state; a genuinely distinct nested
  post would now remain visible as a row rather than being silently discarded.

Citations:

- Implementation: [`www_grid_projection.py`](../../forseti-harness/capture_spine/reddit_subreddit_grid/www_grid_projection.py), especially
  `WWW_GRID_PROJECTION_PARSER_VERSION`, `_WwwRedditGridParser.handle_starttag`,
  and `_WwwRedditGridParser._finish`.
- Regression evidence: [`test_www_grid_projection.py`](../../forseti-harness/tests/unit/test_www_grid_projection.py), especially
  `test_ad_with_reddit_permalink_is_still_excluded`,
  `test_duplicate_permalink_is_one_semantic_row`,
  `test_nested_duplicate_post_element_is_one_semantic_row`, and
  `test_a_missing_end_tag_does_not_silently_swallow_later_posts`.
- Cross-vendor finding, home-model adjudication, validation, and landing:
  [PR #1511](https://github.com/eric-foo/forseti/pull/1511).

## v7 — transient canary; never landed

Legacy stored identifier: `www-7`

- `+` Demonstrated that excluding a permalink-bearing promoted element repairs
  the observed 128-elements / 127-rows anomaly.
- `+` Added canonical-URL deduplication for duplicate post shells.
- `-` Coupled the element count to row finalization, weakening the count as an
  independent failure witness.
- `-` Added nested-post suppression that could silently absorb later independent
  posts after malformed markup. This defect prevented v7 from landing.

Citations:

- Immutable Aug 22 canary packet: content record
  `F:\forseti-data-lake\raw\14a\01M0MN16B3DGE69CE510C94MWG\raw\03_content_record.json`.
- Pre-repair comparison packet:
  `F:\forseti-data-lake\raw\8c8\01M0MMKX07YVB53H9M60XHTE12`.
- The v7 failure analysis and v8 correction were adjudicated and landed in
  [PR #1511](https://github.com/eric-foo/forseti/pull/1511).

## Earlier versions

Versions v1–v6 predate this explanatory ledger. Their exact behavior remains
recoverable from Git history. This changelog makes no retrospective claims about
them beyond the current source's rule that every behavior change bumps the
parser identifier.
