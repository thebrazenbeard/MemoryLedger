# MEMORY_LIFECYCLE_CONTRACT_V0

**Scope:** source-only, synthetic, no installed interface, no external effects, no autobiographical admission.

## Purpose

An advisory lifecycle **proposal** plane connecting source evidence to possible memory review. It must not become another storage engine. STM owns working context; Vera Mono owns current governed-memory admission; DeepMemoryStorage is a historical evidence plane. Roots/Ingest support provenance and source custody.

A repository or tool being discoverable does not mean Vera can invoke it. A tool's invocation does not establish human consent. A stored row does not establish truth, current identity, or model consumption.

## Nonnegotiable invariants

1. The producer's authenticated principal, tenant, project, identity, session, source, privacy scope, consent and operation purpose come from a trusted host, **never** from model-authored text or filenames.
2. Every authority check is re-evaluated for the proposed operation; revoked or expired grants cannot authorize memory export.
3. Byte custody, historical origin, interpretation, currentness, user approval, memory admission and model consumption are **different evidence classes**. Do not promote one into another.
4. A quotation, joke, question, hypothetical, roleplay or instruction is not automatically a new autobiographical memory. An assertion is only a **candidate for review**.
5. Event time, document creation time, observed time, review time and correction time remain distinguishable. Recency is not authority.
6. Corrections preserve origin and cannot silently reset retention. Unknown, mismatched, temporally impossible or cyclical corrections are held for review.
7. If a memory source has expired under the host's policy, a pending/failed handoff does not extend its lifetime.
8. A private transcript must never be written to the public DeepMemoryStorage GitHub repository or this public laboratory.
9. The plan must not contain raw content, private locators, tools, credentials or execution receipts.
10. No automatic source absorption, model calling, training, memory export, effect authorization, service activation or Vera Mono mutation.

## Data and trust contracts

**ConversationEvent:** immutable opaque event/source IDs, SHA-256 content digest, speaker label, tenant/project/identity/conversation, timezone-aware occurred_at, privacy scope and advisory speech-act. Correction target is optional only for CORRECTION. Structural validity is **not** authenticity.

**HostAuthorization:** returned by an injected, host-owned verification callback, with principal, exact tenant/project/identity/conversation, granted privacy labels, purposes, consent ref, issuance and expiry times, and revocation flag. A Python object or matching field string cannot authenticate itself. A model-controlled authorizer is invalid by architecture.

**LifecyclePolicy:** optional host-supplied historical-review eligibility and local-source expiry windows, **not** global retention defaults. The selected STM 30/45 policy may be passed explicitly for applicable opt-in records. Review never equals transfer.

**CandidateIndex:** bounded to 1,024 distinct event IDs per snapshot. It is an untrusted structural snapshot unless a host establishes completeness, source authority, privacy eligibility, tombstones and version/cursor binding.

**LifecycleProposal:** opaque event ID, content digest, disposition and coded reason, optional correction target. Claim ceiling is PROPOSAL_ONLY_NO_MEMORY_ADMISSION_OR_EFFECT. EXPIRE is a **recommendation**, not an implemented deletion.

## Deterministic decision order

- Absent/exceptional injected host authorization -> HOLD.
- Project/identity/tenant/conversation mismatch, unauthorized privacy, revoked/stale/not-yet-issued consent -> HOLD.
- Event timestamp after host observation -> HOLD. A duplicate unchanged event -> HOLD; same ID with conflicting content or identity -> REJECT collision.
- A source beyond explicitly configured expiration -> propose EXPIRE, not export.
- Correction with absent, ambiguous, cross-scope, postdated, expired or cyclic source -> HOLD; valid correction -> REVIEW_CORRECTION only with explicit purpose.
- Assertion eligible for historical review and with purpose -> REVIEW_HISTORICAL. Otherwise assertion with current-review purpose -> REVIEW_CURRENT.
- Other pragmatic classes -> WORKING_ONLY only if purpose allows it, else HOLD.

No branch performs I/O or persists a result.

## Qualification required before any private installation

1. Exact source/binary identity of selected Vera Mono route and host runtime, no reliance on donor-repo labels or CI alone.
2. Real, independently authenticated principal/session/tenant/privacy with denied principal, revoked consent and wrong-root negative tests.
3. Immutable memory DB owner project/identity and cross-project reader/supersession confinement; migration of existing ledgers without private content publication.
4. Source byte custody, original time/provenance, complete correction and tombstone scope; bounded input, clocks, index and output.
5. Transactional reservation/readback for real effects: RESERVED -> COMPLETED or OUTCOME_UNKNOWN, safe restart reconciliation and no blind duplicate transfers.
6. Real private revocable/encrypted historical sink and STM retention, correction, WAL/cache/backup cleanup and deletion proof.
7. Frozen exact-head independent review, host-installed synthetic allow/deny/replay/revoke tests, model consumption evidence if that claim is made, and reversible rollout.

This lab is **not qualified** for any of the above yet.
