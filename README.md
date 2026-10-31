# MemoryLedger

**Status: design scaffold — no executable memory service on `main`.**

MemoryLedger is a proposed, model-agnostic boundary for deciding whether a referenced conversation or other source record may become a persistent memory candidate. The intended reusable product is an evidence-and-review workflow: preserve where a claim came from, keep the original scope and remembering preference, and require an independently authorized decision before historical evidence is admitted to memory.

The repository is **not** a memory backup, a private conversation archive, a trained model, or a deployed authorization service.

## What is available today

As of the `main` revision inspected on 2026-10-31, this repository contains only [`.gitignore`](.gitignore). There is no root README prior to this proposed documentation change, and no committed application source, test suite, package manifest, database schema, HTTP/MCP service, CLI, or license on `main`.

Development proposals in separate branches or Draft PRs are **not** part of the released `main` implementation. Evaluate their exact source and tests before relying on any proposed interface.

## Intended reusable workflow

The following is a design boundary, **not an executable API**:

1. **Reference a source.** Record an opaque source identifier, owner/tenant scope, source role, and a digest or locator that can be checked against the original. Avoid copying entire conversations into public artifacts.
2. **Preserve intent and provenance.** Keep the source's original remember preference, privacy scope, chronology, and uncertainty separate from any later model summary.
3. **Triage conservatively.** Unknown or denied remembering, untrusted origin, or an unsupported role must not silently become an admitted memory.
4. **Require independent review.** Historical admission needs authenticated host evidence, purpose-specific authorization, and an explicit review/consent receipt; a model's own statement is insufficient.
5. **Retain correction and revocation history.** Later corrections should link to the earlier decision and must not rewrite uncertain historical material into a supposedly current fact.
6. **Authorize each downstream use separately.** Admission to a historical ledger does not grant permission to train model weights, disclose a record, call a tool, or perform an effect.

An illustrative decision path is:

```text
source reference -> provenance check -> consent/scope review
                -> historical candidate or quarantine
                -> separately authorized consumer decision
```

This is a proposed product contract, not proof of implemented validation, durable append-only storage, or tamper-resistant enforcement.

## Security and privacy boundaries

- **Host-owned authority:** The embedding host, not a model-generated record or mutable adapter, must authenticate actors and bind owner, model/provider, runtime instance, consent, and allowed effects.
- **No implicit inheritance:** Permission for one model, source, person, purpose, or moment cannot be transferred to another by reusing a ledger key or document.
- **Historical is not current:** A correctly cited old preference, relationship, or identity statement cannot certify present consent or truth.
- **Data minimization:** Use synthetic records when testing and publishing examples. Protect raw private archives and source identifiers through separately enforced access controls.
- **No deployment claims:** This `main` branch provides no network service, cryptographic ledger, host-enforced consent gate, retention scheduler, or verified cross-repository data transfer.

## Development and qualification

The first implementation milestone would be a small, local, synthetic-record contract that rejects unsupported admission and records review decisions. It would need negative tests for forged roles, changed owner scope, unknown/revoked consent, source-digest mismatches, replay, and unauthorized downstream effects, followed by independent host integration testing.

There are currently **no tests to run from `main`**. A passing test in an unmerged proposal applies only to that exact proposal head; it cannot qualify the default branch or a deployed host.

## Licensing

No repository-wide `LICENSE` file is present on the inspected `main` revision. Public visibility does not itself grant redistribution, commercial-use, or derivative-work rights. Obtain the owner's permission or an applicable license before repackaging this work.
