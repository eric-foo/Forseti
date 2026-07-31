# Summer Fridays Understanding p11r1 — CO1 Recovery Delta

```yaml
retrieval_header_version: 1
artifact_role: Company-core acquisition recovery return
scope: Settles only the three CO1 jobs left pending by p11: CO1-J2, CO1-J10, and CO1-J11.
use_when:
  - Combining the immutable p11 CO1 return with p11r1 recovery evidence.
authority_boundary: retrieval_only
```

## Terminal Accounting

```yaml
status: BLOCKED_TERMINAL
parent_jobs: {planned: 11, completed: 8, blocked: 3, unrun: 0}
p11r1_pending_jobs: {planned: 3, completed: 1, blocked: 2, unrun: 0}
combined_jobs: {planned: 11, completed: 9, blocked: 2, unrun: 0}
completed_job_ids: [CO1-J2]
blocked_job_ids: [CO1-J10, CO1-J11]
```

## CO1-J2 — Public Ownership And Leadership Boundary

Three fresh, hash-valid packets complete the bounded public-source job:

| Packet | Packet ID | Manifest SHA256 | What it establishes |
|---|---|---|---|
| TSG 2024 investment release | `01KYWW25RD9NCFJSTZDZG8EP9K` | `7c6fd2cf50f9c480a7b22978ea0e1df94da4d5aa20f4fa6539235cff1fc508d8` | TSG made a strategic growth investment in July 2024; the founders retained a significant stake and continued to lead; Prelude exited; the release named then-current executive roles. |
| Current TSG partner page | `01KYWW34Q4F4NBSGPMGFV78389` | `c5b02814a90f9324ddc9c179a659eef6b3f2ff452639a982f7257652b2e09b0d` | TSG currently presents Summer Fridays as a partner and identifies founders and a management team, but states neither stake nor legal control. |
| California records scope | `01KYWW3TNRX0S0ZW9ZSGP8Z9CE` | `53c7ac543258e98b8da950c04c84edb84b6e350114cb22848fbcd97b1f8bba17` | The official state records authority does not make ownership, shareholder, employee, or operating-agreement information part of the public business record. |

The complete bounded finding is narrow: TSG's July 2024 investment, founder
stake, and then-current role statements are established for that date, and a
current TSG surface still uses public partnership language. Current legal
control, current ownership percentages, and current executive-title currency
were not established by the bounded company, investor, and official-record
sources. That is a public-evidence limit, not a claim that the real ownership
or roles are unknowable.

## CO1-J10 And CO1-J11 — Owned Pages

The child runner now preserves safe response metadata before judging content.
Both first attempts returned HTTP 429 with `Retry-After: 60` and the exact typed
reason `local_rate_limited`:

| Job/attempt | Packet ID | Manifest SHA256 | Result |
|---|---|---|---|
| CO1-J10 initial | `01KYWW0EDRFYPCAW8BAJFCJD1H` | `9035bf41996055a4b94fcab8b5f1b7a8fec2775e3533d6a54ee0deacd96f8092` | 429, 18-byte rate marker, no source body. |
| CO1-J11 initial | `01KYWW0ZA2NQS5FQ83YS7B44EE` | `724eb7d91842941a90b7240217e3cfbc1c05dbb8ebfd332840c908f5b5251eca` | 429, 18-byte rate marker, no source body. |
| CO1-J10 final recovery | `01KYWWCYGVGSK9RP67K37YDCJ7` | `0b00ad7f1236acc672d11761dfc1e9c42106caa6da60a08ced6ae2c22759d2ad` | After the full backoff, 429 recurred with `Retry-After: 60`; shared route stopped. |

The two initial calls were launched 15 seconds apart before the first response
metadata was inspected. That was an orchestration error: the second call did
not honor the newly observed backoff. It is preserved here rather than hidden.
The final J10 recovery did honor the full backoff; its repeated 429 opened the
shared-host circuit, so J11 was not retried again. Neither owned-page body was
acquired, and SERP snippets do not substitute for it.

Raw packets live under
`C:\tmp\forseti-summer-fridays-understanding-p11r1-20260801\specialists\co1\`.
