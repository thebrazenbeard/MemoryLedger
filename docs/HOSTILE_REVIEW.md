# Hostile review — MemoryLedger v0 synthetic source candidate

This is a **design instrument**, not an independent review, deployment qualification, or live model-memory test.

## Red/green evidence (local stdlib Python)

The initial assertion test failed against a HOLD/NOT_IMPLEMENTED stub and passed after implementing LifecyclePlanner. A later three-test batch for correction of expired sources, correction of future targets, and correction cycles failed against the initial implementation, then passed after the guarded behavior was added. Candidate-index overflow also failed before bounding and passed afterward.

Initial frozen head: **31 synthetic tests passed**. After reviewer found an unhandled three-event correction cycle at exact prior head, seven additional adversarial tests were introduced: the six failing negatives were observed RED, then the revised bounded ancestry traversal passed all **38** synthetic tests in a freshly cloned GitHub branch on Lappy. No real private conversations, provider accounts, SQLite memory databases or model calls were part of the suite. A frozen remote revision must be tested again before merging.

## Adversarial cases and expected invariant

| Attack / confusion | Source test | Expected result |
| --- | --- | --- |
| Missing host authentication, exception, fabricated dictionary allow | test_no_host_authorizer_*, test_host_callback_*, test_unexpected_host_grant_* | HOLD |
| Cross-tenant, cross-project, cross-identity or cross-conversation | test_cross_project_identity_* | HOLD |
| Unauthorized privacy scope | test_privacy_scope_* | HOLD |
| Expired/future-issued or revoked grant | test_expired_future_issued_* | HOLD |
| Quotation, joke, hypothetical, instruction, question, unknown speech act | test_quote_hypothetical_* | At most WORKING_ONLY |
| Asserted fact falsely treated as admitted current truth | test_assertion_can_only_* | REVIEW_CURRENT proposal only |
| No explicitly configured age policy | test_no_global_policy_* | No invented global expiration |
| Explicit day-30 review versus day-45 expiry | test_historical_review_*, test_day_45_* | Review, then EXPIRE proposal; no export |
| Same event replays, same ID different content or identity | test_idempotent_replay_*, test_same_id_* | HOLD or REJECT |
| Cross-privacy correction, unknown target | test_cross_identity_correction_*, test_unknown_correction_* | HOLD |
| Retention extension by later correction | test_correction_cannot_restart_* | HOLD |
| Future correction target or correction cycle | test_correction_cannot_claim_*, test_correction_cycle_* | HOLD |
| Unbounded/duplicate candidate index IDs | test_unbounded_candidate_*, test_ambiguous_duplicate_* | Reject snapshot |
| Path-like IDs, bad digest, naive timestamps, mutable grants | test_invalid_identity_*, test_naive_timestamp_*, test_mutable_scope_* | Reject contract construction |
| Planner doing file/network/DB writes | test_pure_planning_does_not_invoke_* | No I/O |
| Result leaking source locator or raw text | test_review_result_carries_* | Omit sensitive material |

## Strongest surviving objections

> **1. A malicious caller can inject an always-allow host callback and self-authorize. Accepted.** These Python types do not certify authenticated host authority. Production host composition must hold the authorizer private, authenticate real caller/session, bind tenant/consent/privacy and separately validate effects. This library cannot solve a malicious host.

> **2. Semantic and pragmatic labels can be wrong. Accepted.** A model can rephrase a quotation as a user belief. The planner considers labels as advisory and never automatically admits current memory. Future interpretation must preserve original utterance, speaker attribution, provenance and independent review.

> **3. A bounded index may omit material contradictions, revoked grants and tombstones. Accepted.** Structural bounds are not evidence completeness. The host must provide versioned, complete authorized snapshots and enforce revocation at the operation boundary.

> **4. Expiration advice does not implement deletion. Accepted.** EXPIRE does not delete STM, SQL WAL, FTS, backups, caches or an external sink. A separately authorized retention controller needs full readback and residual-copy accounting.

> **5. Public repository is an attractive accidental exfiltration path. Accepted.** Never add actual conversation contents, memory exports, private credentials, or user-specific evaluation material. Use synthetic cases only.

> **6. Existing Vera Mono memory DB can be misbound by project/identity at the same root. Accepted.** Separate physical Lappy synthetic checks of an older installed module demonstrated cross-identity reads and supersession. This planner avoids raw DB access, but a future adapter must fix/test immutable store ownership and reader/writer scoping independently.

> **7. CI and green unit tests could falsely qualify runtime consumption. Accepted.** This source has no service, QVR host binding, historical sink, model runtime, durable effect receipts, private consent or independent deployment witness. Those remain HOLD.

## Evidence classes

- SOURCE_INSPECTION: reference implementation contracts from STM, DeepMemoryStorage, Vera Mono, Roots and Ingest; freshness must be checked again at absorption.
- TEST: 38 stdlib synthetic tests after review-driven correction-chain repair, with new RED-to-GREEN evidence; no independently labeled comparative history benchmark.
- REVIEW: separate reviewer reported exact-prior-head physical Windows execution, found an unhandled three-event correction cycle, and required independent comparative labels. **No renewed independent review of the corrected head** yet.
- REAL_HOST_SYNTHETIC_TEST: Lappy cloned current branch and 38 tests passed. REAL_SELECTED_VERA_RUNTIME_PROBE: none.
- RUNTIME_CONSUMPTION, MEMORY_ADMISSION, EXTERNAL_EFFECT, DEPLOYMENT: none.

A reviewable draft source branch is a laboratory milestone, not Vera Mono installation permission.

## Review follow-up

The reviewed head `06fe39e` incorrectly returned REVIEW_CORRECTION on a three-event correction cycle. The current Draft PR adds complete bounded ancestry traversal (64-link cap), repeated source-time/identity/privacy/expiry checks and seven new tests. This is **a correction requiring renewed exact-head review**, not proof that the previous reviewer approved the new code. See [COMPARATIVE_EVALUATION_PROTOCOL_V1](COMPARATIVE_EVALUATION_PROTOCOL_V1.md); the matched baseline and independent labels are not yet available.
