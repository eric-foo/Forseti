# CO1 Company Core Final Acquisition Recovery

```yaml
cycle_id: summer_fridays_understanding_p11r3_20260801
actor: CO1
scope: Acquire only the two CO1 jobs still pending after p11r2; no Deliver work.
authority_revision: e39e7ab8c7035759df42f14534c49281106bcc15
planned_job_ids: [CO1-J10, CO1-J11]
completed_job_ids: [CO1-J10, CO1-J11]
blocked_job_ids: []
unrun_job_ids: []
status: COMPLETED_TERMINAL
```

## Result

Both exact, Phase-1-licensed Summer Fridays pages were captured through the
normal Direct HTTP capture spine. Requests were serialized and started 90
seconds apart. Both returned HTTP 200 with their substantive page bodies.

| Job | Source | Final packet | Manifest SHA256 | Body facts |
|---|---|---|---|---|
| `CO1-J10` | `https://summerfridays.com/pages/jet-lag-mask-statement` | `01KYX0BVEC29YY8WJZ54VBHPMC` | `8737361834c16d7d687445a06be4c80f0c698e7a7dc7c18fed6331951c416460` | 512,216 bytes; title `Jet Lag Mask Statement – Summer Fridays`; redness, irritation, and manufacturing terms present. |
| `CO1-J11` | `https://summerfridays.com/pages/sustainability` | `01KYX0EM0Z5HXRQJNP1TJPM8C1` | `953609af043717dc05934cb4c8515f5d6928d91afa86b8879b0cb99376f5cf42` | 522,683 bytes; title `Sustainability | Summer Fridays`; vegan and cruelty-free terms present. |

Final packet paths:

- `C:\tmp\forseti-summer-fridays-understanding-p11r3-20260801\owned_pages_direct_http_validated\01_CO1-J10_packet`
- `C:\tmp\forseti-summer-fridays-understanding-p11r3-20260801\owned_pages_direct_http_validated\02_CO1-J11_packet`

The batch summary SHA256 is
`8fc715c67da13725fd6c19d6b2577f57b9fcb3ba01eb340c5c6767355d478fab`.
Both metadata records report `body_classification=content_unverified`, which is
the classifier's honest ceiling; neither reports a block signal or limitation.

## Preserved Diagnostic Attempts

The first p11r3 pair is preserved under `owned_pages_direct_http`. Each body was
the full requested Shopify page, but the then-current generic classifier treated
a dormant `hcaptcha` script reference as a challenge shell. Those packets remain
valid provenance but receive no completion credit because their manifests carry
that false limitation. Their manifest SHA256 values are
`a6e0d05f7f2a844625a49ee2867991637654b1a5dd8913902c5e9d42a09666f9`
and `21b59ad7cac2637739d7267a2f03652e2457965fdfdb83e6c43f8360db48a37b`.

No page claim is synthesized here. This is an acquisition return only.
