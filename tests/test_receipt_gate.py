"""Synthetic adversarial checks for cross-store custody and revocation plans."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from memoryledger.receipt_gate import (
    HistoricalReceipt, ReceiptStatus, RevocationAck, SourceCustody,
    plan_historical_handoff, plan_revocation_reconciliation,
)


NOW = datetime(2026, 11, 5, tzinfo=timezone.utc)
HASH = "a" * 64
KEY = "b" * 64
MAC = "c" * 64


def source(**kwargs):
    fields = dict(tenant_id="tenant:synthetic", owner_id="owner:synthetic",
                  agent_id="agent:synthetic", source_id="source:synthetic",
                  source_version_digest=HASH, privacy_scope="private:owner",
                  source_scope="PROJECT_BOUND", native_project_id="project:synthetic",
                  native_project_id_verified=True,
                  recorded_at=NOW - timedelta(hours=1),
                  expires_at=NOW + timedelta(days=1))
    fields.update(kwargs)
    return SourceCustody(**fields)


def receipt(**kwargs):
    fields = dict(destination_id="dms:historical", source_version_digest=HASH,
                  idempotency_key=KEY, external_record_id="record:synthetic",
                  receipt_mac=MAC)
    fields.update(kwargs)
    return HistoricalReceipt(**fields)


def handoff(s=None, r=None, **kwargs):
    kwargs.setdefault("project_verifier", lambda *_: True)
    return plan_historical_handoff(s or source(), r if r is not None else receipt(),
                                   destination_id="dms:historical",
                                   expected_idempotency_key=KEY, at=NOW, **kwargs)


def ack(destination="dms:historical", **kwargs):
    fields = dict(destination_id=destination, source_version_digest=HASH,
                  operation="ERASE_SOURCE", receipt_mac=MAC)
    fields.update(kwargs)
    return RevocationAck(**fields)


class ReceiptGateTests(unittest.TestCase):
    def test_caller_project_verified_flag_needs_separate_host_probe(self):
        result = plan_historical_handoff(source(), receipt(),
            destination_id="dms:historical", expected_idempotency_key=KEY,
            at=NOW, verifier=lambda *_: True)
        self.assertEqual(result.status, ReceiptStatus.HOLD)
        self.assertEqual(result.reason, "INDEPENDENT_PROJECT_VERIFIER_REQUIRED")
        for project_verifier in (lambda *_: False, lambda *_: 1,
                                 lambda *_: (_ for _ in ()).throw(RuntimeError())):
            outcome = handoff(verifier=lambda *_: True, project_verifier=project_verifier)
            self.assertEqual(outcome.reason, "PROJECT_BINDING_VERIFICATION_FAILED")

    def test_historical_only_after_injected_independent_verification(self):
        self.assertEqual(handoff().status, ReceiptStatus.HOLD)
        self.assertEqual(handoff(verifier=lambda *_: False).status, ReceiptStatus.HOLD)
        self.assertEqual(handoff(verifier=lambda *_: 1).status, ReceiptStatus.HOLD)
        self.assertEqual(handoff(verifier=lambda *_: (_ for _ in ()).throw(ValueError())).status,
                         ReceiptStatus.HOLD)
        decision = handoff(verifier=lambda s, r: s.source_version_digest == r.source_version_digest)
        self.assertEqual(decision.status, ReceiptStatus.HISTORICAL_REVIEW_ONLY)
        self.assertEqual(decision.effect, "PROPOSAL_ONLY_NO_STORE_OR_MEMORY_EFFECT")
        self.assertNotIn("ADMITTED", decision.status.value)

    def test_forged_receipt_bindings_fail_without_invoking_verifier(self):
        for bad in (dict(destination_id="dms:other"),
                    dict(source_version_digest="d" * 64),
                    dict(idempotency_key="e" * 64)):
            with self.subTest(bad=bad):
                calls = []
                decision = handoff(r=receipt(**bad), verifier=lambda *_: calls.append(1) or True)
                self.assertEqual(decision.reason, "RECEIPT_BINDING_MISMATCH")
                self.assertEqual(calls, [])

    def test_missing_native_project_id_holds_instead_of_inventing_one(self):
        unresolved = source(native_project_id=None, native_project_id_verified=False)
        result = handoff(s=unresolved, verifier=lambda *_: True)
        self.assertEqual(result.status, ReceiptStatus.HOLD)
        self.assertEqual(result.reason, "NATIVE_PROJECT_ID_UNVERIFIED")
        self.assertEqual(handoff(s=source(source_scope="UNKNOWN"), verifier=lambda *_: True).status,
                         ReceiptStatus.HOLD)

    def test_true_global_scope_can_handoff_without_project_but_not_fake_global(self):
        global_source = source(source_scope="GLOBAL", native_project_id=None,
                               native_project_id_verified=False)
        self.assertEqual(handoff(s=global_source, verifier=lambda *_: True).status,
                         ReceiptStatus.HISTORICAL_REVIEW_ONLY)
        fake = replace(global_source, native_project_id="project:invented")
        self.assertEqual(handoff(s=fake, verifier=lambda *_: True).reason,
                         "GLOBAL_SOURCE_WITH_UNEXPECTED_PROJECT_CLAIM")

    def test_expired_handoff_holds_but_erasure_still_required(self):
        expired = source(expires_at=NOW - timedelta(seconds=1))
        self.assertEqual(handoff(s=expired, verifier=lambda *_: True).reason,
                         "SOURCE_NOT_CURRENT_FOR_HANDOFF")
        pending = plan_revocation_reconciliation(expired, destinations=("dms:historical",),
                acknowledgements=(), at=NOW, verifier=lambda *_: True)
        self.assertEqual(pending.status, ReceiptStatus.PENDING_REVOCATION_ACKS)

    def test_future_source_cannot_receive_retroactive_revocation_ack(self):
        future = source(recorded_at=NOW + timedelta(hours=1),
                        expires_at=NOW + timedelta(days=1))
        result = plan_revocation_reconciliation(future, destinations=("dms:historical",),
                acknowledgements=(ack(),), at=NOW, verifier=lambda *_: True)
        self.assertEqual(result.status, ReceiptStatus.HOLD)
        self.assertEqual(result.reason, "SOURCE_NOT_YET_RECORDED")

    def test_unresolved_project_does_not_orphan_existing_custody_on_revocation(self):
        unresolved = source(native_project_id=None, native_project_id_verified=False)
        result = plan_revocation_reconciliation(unresolved, destinations=("dms:historical",),
                acknowledgements=(ack(),), at=NOW, verifier=lambda *_: True)
        self.assertEqual(result.status, ReceiptStatus.ACKS_VERIFIED_REVIEW_ONLY)

    def test_partial_revocation_never_claims_complete(self):
        destinations = ("dms:historical", "stm:archive")
        partial = plan_revocation_reconciliation(source(), destinations=destinations,
            acknowledgements=(ack(),), at=NOW, verifier=lambda *_: True)
        self.assertEqual(partial.status, ReceiptStatus.PENDING_REVOCATION_ACKS)
        self.assertEqual((partial.acknowledged, partial.required), (1, 2))
        done = plan_revocation_reconciliation(source(), destinations=destinations,
            acknowledgements=(ack(), ack("stm:archive")), at=NOW, verifier=lambda *_: True)
        self.assertEqual(done.status, ReceiptStatus.ACKS_VERIFIED_REVIEW_ONLY)
        self.assertEqual(done.effect, "PROPOSAL_ONLY_NO_STORE_OR_MEMORY_EFFECT")

    def test_rogue_duplicate_wrong_digest_and_forged_ack_fail_closed(self):
        destinations = ("dms:historical",)
        bad_cases = [((ack("rogue:other"),), "ACK_TARGET_UNEXPECTED_OR_DUPLICATE"),
                     ((ack(), ack()), "ACK_TARGET_UNEXPECTED_OR_DUPLICATE"),
                     ((ack(source_version_digest="d" * 64),), "ACK_SOURCE_DIGEST_MISMATCH"),
                     ((ack(operation="REVOKE_SCOPE"),), "ACK_OPERATION_MISMATCH")]
        for acks, reason in bad_cases:
            with self.subTest(reason=reason):
                outcome = plan_revocation_reconciliation(source(), destinations=destinations,
                          acknowledgements=acks, at=NOW, verifier=lambda *_: True)
                self.assertEqual(outcome.reason, reason)
        for verifier in (None, lambda *_: False, lambda *_: 1,
                         lambda *_: (_ for _ in ()).throw(RuntimeError())):
            self.assertEqual(plan_revocation_reconciliation(source(), destinations=destinations,
                acknowledgements=(ack(),), at=NOW, verifier=verifier).status,
                ReceiptStatus.HOLD)

    def test_incomplete_or_duplicate_destination_inventory_refused(self):
        for destinations in ((), ("dms:historical", "dms:historical")):
            with self.assertRaises(ValueError):
                plan_revocation_reconciliation(source(), destinations=destinations,
                   acknowledgements=(), at=NOW)
        with self.assertRaises(ValueError):
            plan_revocation_reconciliation(source(), destinations=tuple(f"dms:{i}" for i in range(65)),
                                           acknowledgements=(), at=NOW)

    def test_returned_plan_never_echoes_private_owner_or_source_ids(self):
        decision = handoff(verifier=lambda *_: True)
        rendered = repr(decision)
        self.assertNotIn("tenant:synthetic", rendered)
        self.assertNotIn("owner:synthetic", rendered)
        self.assertNotIn("source:synthetic", rendered)
        self.assertNotIn(HASH, rendered)
        self.assertNotIn(MAC, rendered)


if __name__ == "__main__":
    unittest.main()
