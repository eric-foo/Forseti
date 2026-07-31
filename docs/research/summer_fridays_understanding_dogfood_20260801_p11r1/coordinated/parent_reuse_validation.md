# Summer Fridays Understanding p11r1 — Parent Reuse Validation

```yaml
retrieval_header_version: 1
artifact_role: Confirm-don't-trust validation of the immutable p11 acquisition parent
scope: Records the fresh validation that licenses reuse of completed p11 work while giving no completion credit to its blocked seal.
use_when:
  - Auditing which p11 artifacts p11r1 reused instead of rerunning.
authority_boundary: retrieval_only
```

## Authority And Result

The commissioned parent was read from its existing launch root at commit
`91fce81459a58528c3ead10d8a5ac5e45c96824a`. Its acquisition authority remains
`aa92073b51c3a4259fbc800e98a06770ec21fb8b`; the later commit only records a
locality nonclaim and does not replace that bound acquisition authority.

Fresh checks observed:

- commission-board validation: `PASS`;
- parent `phase_acquisition_seal_v2` validation: `PASS`;
- raw closure: 232 manifest locations, 188 unique packet IDs, and 933
  preserved-file declarations, with zero parse, missing-file, size, or SHA256
  errors;
- bounded parent raw/durable Deliver-name scan: no Deliver, synthesis, Phase B,
  or Turn B artifact found.

The parent seal has canonical-text SHA256
`462df7b3ffe1e5dea5661e9fc4dc839bcd96c437fb433dec166f46f0d66eea2f` and
state `BLOCKED_ACQUISITION_INCOMPLETE`. It is provenance, not evidence that
Phase A completed. Only parent jobs already recorded complete were reused;
the 14 parent pending IDs were the p11r1 execution set.

## Fresh-Read Artifact Register

Hashes below use the acquisition-seal text convention: Markdown, JSON, and
YAML line endings are canonicalized to LF before SHA256 comparison.

| Parent artifact | SHA256 |
|---|---|
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/coldness_provenance.md` | `570a540633adf53b199223472614cb56bbcacdd407e9a87affeae436ef0e6128` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/commission_board.md` | `81a2f3b0a64c5258a2643429f72e4ddbaf4813ae3bc8b0cef60f6fded933ebbf` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/run_cost_log.md` | `2de16b642d83db88f7a40124d38a61fbc32fabb181a4f7501c0e8d86b2688f27` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/competitor_ledger.json` | `b683b559f33aa4aade4209126e0d10662411aacc99852e79074ef4a949c8255f` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/cost_log.md` | `967bc08e622812e078b133e9f34341ae1fb293d96967076164324c7fcb954495` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase1/scout_return.md` | `c411b00df7952a86de7983f9e3d4138fe249e695719fa31247738aeb73354ce7` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/decision_receipt.json` | `3e814232972ecedec7c563f79c78bfca70f9618fae5b5a6c17446345f1dc95bf` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/lifecycle_provenance.json` | `0e37cd5a6e6fd064d5d2c08d1f27b2200e2ce2c9e61670e2b53b20ed48ce44ec` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/targeted_return.md` | `e5fc7bb42a96c103328764ca10536fe16fa0fa49f3b1633b556e9313c851d9a7` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co1_company_core_identity.md` | `42fdf0f8c89ff573b62ce250e94e521a1ead8b9b6f5142ad0184a63799d0fb80` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md` | `b76c772fd7227621938516f6ff1b5fa3c94e2f082392d257e7072d6eda23b880` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co3_customer_community_depth.md` | `6fa6f693e30f2a7c1fb11ba2e848d4d6cbaf04e42ae48918f83ed6bec862847b` |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/turn_a_acquisition_record.md` | `7557714771cc7f11aade0c62e4dc98c643c877124ee7904e76df1cf74043031e` |
| `docs/workflows/summer_fridays_understanding_dogfood_20260731_p11/coordinated/acquisition_seal.md` | `462df7b3ffe1e5dea5661e9fc4dc839bcd96c437fb433dec166f46f0d66eea2f` |

## Checkout Finding

A fresh Windows checkout preserved the same Git blobs but rendered text files
with CRLF line endings, which made the old exact-byte verifier report false
hash drift. The p11r1 hardening changes the seal verifier only for text
artifacts: it compares canonical LF bytes for Markdown, JSON, and YAML while
retaining exact-byte checks for every other suffix. The parent seal then passes
both in its original launch root and in the fresh child checkout; a real text
edit remains a hash mismatch.
