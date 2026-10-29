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

## Design boundaries

- A host-injected authorizer callback does not authenticate itself. It must be selected, constrained and verified by a trusted host, independently of any LLM.
- Event speech-act labels (hypothetical, quotation, assertion, joke, instruction, correction) are **candidate interpretations**. They do not prove original speaker intent or source truth.
- Assertions may only trigger a **review** proposal, never automatic autobiography or durable memory admission.
- Correction review cannot target another project/identity/privacy scope, future source, expired source, or a cycle.
- Optional age windows belong to the **selected host policy**. A synthetic day-30 review/day-45 expiry test does not impose those durations globally.
- No real STM-to-DMS handoff exists here; transfer must be explicitly consented, private, reversible/revocable, receipt-bearing and verified elsewhere.
- Proposal outputs omit raw conversation text, private source locators and operational authority. No effects or new memories can be produced by this planner.

See [MEMORY_LIFECYCLE_CONTRACT_V0](docs/MEMORY_LIFECYCLE_CONTRACT_V0.md) and [HOSTILE_REVIEW](docs/HOSTILE_REVIEW.md).

**Evidence ceiling:** passing these tests establishes synthetic **source behavior only**. It does not establish authentic host identity/consent, filesystem safety, private destination, policy admission, Lappy installation, production model consumption, memory learning or deployment.

Do not add private conversation transcripts or personal memories to this public repository. Any future Vera Mono absorption requires separate exact-source implementation review, host-bound negatives and authorized deployment/rollback verification.
