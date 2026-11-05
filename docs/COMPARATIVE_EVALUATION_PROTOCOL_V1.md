# Comparative memory-decision qualification protocol v1

**Status:** preregistration requirements and execution interface only. No independent held-out cases, ground-truth labels, matched STM/Vera Mono baseline, or production effect evidence has been obtained. **IMPROVEMENT_UNPROVEN.**

## Why this exists

A unit test demonstrating that MemoryLedger proposes `HOLD` for a known hypothetical does not demonstrate better recall, fewer wrongful admissions or less privacy leakage than existing STM plus Vera Mono. The improvement proposition requires a **falsifiable paired evaluation**, not another test suite teaching the model its own labels.

## Sequence (do not reorder)

1. **Freeze** the candidate exact Git commit, STM baseline commit, Vera Mono commit, model/provider identities (if used), evaluator code, time/token budget and real host configuration. Revalidate sources after any change.
2. **Separate custody:** an evaluator independent of the implementing worker creates and labels held-out cases *after* candidate freeze. Preserve label authority, source provenance, privacy grants and adjudication rationale in a private, restricted dataset. The implementation cannot see labels before generating outputs.
3. **Predeclare** case count, composition, inclusion/exclusion criteria, adjudication conflicts, primary metric, no-regression gates, thresholds and statistical uncertainty method before running either arm. No post-result selection.
4. Execute both arms on exactly the same authenticated inputs, host-selected scope, chronological snapshots, consent state, policy and resource budget. Provide exact case IDs, opaque input digests, timestamps and artifact IDs. Log missing cases and ambiguous outcomes rather than deleting them from denominators.
5. Independent custodian checks outcome/source identity, masks private content in reports, adjudicates disagreement without using model agreement as evidence and releases paired per-case scores plus aggregate confidence/uncertainty.
6. **Block promotion** if any protected-boundary regression exists, if case/custody mismatches remain, if baseline was not a real qualified route, or if a positive result depends on label leakage, leakage of future timestamps, cheating by excessive abstention or unmatched budgets.
7. Have a separately authorized reviewer bind exact frozen artifacts to a specific native Vera Mono integration candidate. Source benchmark acceptance alone does **not** grant code merge, install, memory admission, or deployment authority.

## Required cases and outcomes

- Exact user assertions versus quotes, jokes, hypotheticals, questions, model-generated claims and instructions.
- Corrections of current, expired and missing predecessors; 2-node, 3+-node and self-referential cycles; chains beyond the planner's 64-link limit; cross-identity ancestors.
- Unchanged replay, same ID/different digest, incomplete snapshots, rescinded consent, wrong tenant/project/privacy scope, clock rollback and source provenance ambiguity.
- Historical versus current state, conflicting relationships/preferences, speaker substitutions, privacy counterfactuals, adversarial embedded instructions and unseen distributions.
- Retention day-30 review eligibility versus day-45 expiry **only when the actual host selected that policy**; no automatic private export or deletion inference.

Primary paired errors: false current/autobiographical review promotion, unjustified source exposure, missed legitimate correction and correction lineage errors, wrong consent/identity/expiry, and over-abstention that prevents useful recall. Report latency/token budgets and cost, missing outcomes and confidence intervals. Do not add private historical records to this public repository.

## Machine-readable runner requirements (not yet implemented)

An offline comparison harness should accept, from the independent host, these immutable, independently authenticated inputs:

- Evaluation manifest: custodian reference and signature/readback, dataset version/digest, frozen split digest, exact candidate and baseline commits, parser/evaluator version, declared budget and scoring contract.
- Labels: opaque case ID, input/source digest, permitted response classes, protected-boundary expectations, event-time/provenance adjudication and evaluator evidence reference; **not** user-content text in public logs.
- Paired arm receipts: case ID, exact input digest, artifact/model/runtime identity, same constrained budget, decision and no-effect/observed-effect status, receipt ID, failure/timeout or OUTCOME_UNKNOWN.
- Output: paired metrics, all missing/ineligible cases, falsifiers, hard-fail gates, provenance for every score and the exact **claim ceiling**.

The harness must reject mismatched case sets, repeated IDs, changed inputs, unmatched budgets, unverified score receipts or missing label custody. It must never label itself `QUALIFIED` from a caller-supplied string.

## Current hold

No such independently custodied evaluation set or authenticated baseline executor was verified during this PR. The review at [PR #1](https://github.com/thebrazenbeard/MemoryLedger/pull/1) explicitly records that limitation. The executable comparison runner is also not part of v0; any future implementation requires its own failing tests, hostile review and exact artifact readback.

**Claim ceiling:** `EVALUATION_PROTOCOL_ONLY_NO_INDEPENDENT_IMPROVEMENT_EVIDENCE`.
