# MemoryLedger — Vera memory-lifecycle laboratory

**Status: source-only, synthetic-only. Not installed, not a memory database, not a live tool, and not an authorized memory writer.**

MemoryLedger is an independent design/test laboratory for deciding **which lifecycle operation to propose** for attributed conversational evidence. It does not store private conversations or decide what Vera must believe.

Its eventual role is a **memory lifecycle coordinator**, not a fourth memory store:

- STM owns temporary working context and its separately governed optional conversation archive.
- Vera Mono's existing vera_memory package owns current governed-memory admission, CAS heads and supersession.
- DeepMemoryStorage supplies historical evidence. Its public GitHub repository is **not** a private transcript destination.
- Roots and Ingest supply evidence/provenance analysis and byte custody, not truth, consent or identity authority.
- MemoryLedger proposes keep-working, review-current, review-historical, review-correction, hold, reject or expire. **All are proposals, not effects.**

The runtime lineage remains self-contained in Vera Mono. This repository is a donor/research laboratory; no sibling runtime dependency or installation is implied.

## Local synthetic tests

Python 3.11+ and standard library only, no model, service, database, API key, provider, private text, or network required.

```sh
python -m unittest discover -s tests -v
```

The v0 source module is importable as memoryledger. Its public interface is ConversationEvent, HostAuthorization, LifecyclePolicy, CandidateIndex and LifecyclePlanner.propose. It intentionally has no storage, retrieval or export adapter.

### Cross-store receipt gate (synthetic source candidate)

`memoryledger.receipt_gate` adds a **pure advisory seam** between STM's
`STM_HISTORICAL_HANDOFF_CANDIDATE_V1` source envelope and a future, separately
qualified DeepMemoryStorage historical-evidence receiver. It accepts the same
scope identifiers, source-version SHA-256, destination, host-computed idempotency
key and DMS-like receipt fields. The receipt MAC alone is not proof of custody:
an independent, host-selected verifier must authenticate the destination,
receipt MAC, source digest and source/owner scope. Without that verifier the
decision is `HOLD`; a positive result is `HISTORICAL_REVIEW_ONLY`, **not** a
durable write, current-memory admission or evidence of inference consumption.

The gate refuses to infer a native Project ID from source names or timestamps.
A project-scoped historical record whose real native Project ID has not been
verified is held as `NATIVE_PROJECT_ID_UNVERIFIED`; genuinely global sources
must explicitly carry `GLOBAL` scope and no asserted Project ID. This matters
for account exports whose project-scoped records do not identify their project.

`plan_revocation_reconciliation` requires a *host-owned complete destination
inventory* and independently verified per-destination erasure/revocation
tombstone acknowledgements. It remains `PENDING_REVOCATION_ACKS` until every
listed destination is acknowledged, including after source expiry; it refuses
unexpected, duplicate, future-source or wrong-digest acknowledgements. Even a
complete set returns `ACKS_VERIFIED_REVIEW_ONLY`: completeness of the host's
destination inventory, authority and downstream effects are **not** established
by this source module.
An acknowledgement of `REVOKE_SCOPE` cannot silently satisfy an `ERASE_SOURCE`
obligation, or vice versa; the exact expected operation is part of the review.
Revocation remains reviewable when a previously stored source's native Project
ID is unresolved: lost context must not make already-custodied evidence
impossible to erase. The trusted host must still authenticate the source and
every tombstone acknowledgement against its actual custody records.

Run `python -m unittest discover -s tests -v` for all synthetic checks. The
receipt-gate checks exercise forged/missing receipts, Project binding, scope,
expiration, temporal ordering, target completeness and replay-like duplicates.
The module performs **no** file, DB, network, memory, retention, revocation,
deletion or authority mutation. Neither STM nor DMS is imported as a runtime
dependency; their actual wire formats and cryptographic custody must be
requalified together on a private host before use.

## Design boundaries

- A host-injected authorizer callback does not authenticate itself. It must be selected, constrained and verified by a trusted host, independently of any LLM.
- Event speech-act labels (hypothetical, quotation, assertion, joke, instruction, correction) are **candidate interpretations**. They do not prove original speaker intent or source truth.
- Assertions may only trigger a **review** proposal, never automatic autobiography or durable memory admission.
- Correction review cannot target another project/identity/privacy scope, future source, expired source, or a cycle (including longer correction chains; traversal fails closed beyond 64 links).
- Optional age windows belong to the **selected host policy**. A synthetic day-30 review/day-45 expiry test does not impose those durations globally.
- No real STM-to-DMS handoff exists here; transfer must be explicitly consented, private, reversible/revocable, receipt-bearing and verified elsewhere.
- Proposal outputs omit raw conversation text, private source locators and operational authority. No effects or new memories can be produced by this planner.

See [MEMORY_LIFECYCLE_CONTRACT_V0](docs/MEMORY_LIFECYCLE_CONTRACT_V0.md) [HOSTILE_REVIEW](docs/HOSTILE_REVIEW.md), and [COMPARATIVE_EVALUATION_PROTOCOL_V1](docs/COMPARATIVE_EVALUATION_PROTOCOL_V1.md).

**Evidence ceiling:** passing these tests establishes synthetic **source behavior only**. It does not establish authentic host identity/consent, filesystem safety, private destination, policy admission, Lappy installation, production model consumption, memory learning or deployment.

Do not add private conversation transcripts or personal memories to this public repository. Any future Vera Mono absorption requires separate exact-source implementation review, host-bound negatives and authorized deployment/rollback verification.
