import hashlib
import unittest
from candidate_ledger import (
    Candidate, Disposition, LedgerError,
    triage, historical_admission, revoke_historical,
)

def sample(**kwargs):
    data=dict(tenant="local",owner="owner_1",
              source_id="source:conversation-1",message_id="message-1",
              author_role="user",
              sha256=hashlib.sha256(b"synthetic-only").hexdigest(),
              source_scope="global",remember_flag=False)
    data.update(kwargs)
    return Candidate(**data)

class LedgerTests(unittest.TestCase):
    def test_eligible_source_is_review_required_not_automatically_admitted(self):
        result=triage(sample())
        self.assertEqual(result.disposition,Disposition.REVIEW_REQUIRED)
        self.assertEqual(result.evidence_status,"historical_unverified")

    def test_remember_false_explicit_only(self):
        for flag in (None,True):
            with self.subTest(flag=flag):
                self.assertEqual(triage(sample(remember_flag=flag)).disposition,
                                 Disposition.QUARANTINE)
                with self.assertRaises(LedgerError):
                    historical_admission(sample(remember_flag=flag),
                         authenticated_owner="owner_1",reviewer="reviewer_1",
                         consent_receipt="receipt:1",source_integrity_verified=True)

    def test_assistant_internal_role_quarantined(self):
        self.assertEqual(triage(sample(author_role="tool")).disposition,
                         Disposition.QUARANTINE)

    def test_wrong_owner_and_unverified_source_rejected(self):
        c=sample()
        with self.assertRaises(LedgerError):
            historical_admission(c,authenticated_owner="stranger",
                 reviewer="reviewer_1",consent_receipt="receipt:1",
                 source_integrity_verified=True)
        with self.assertRaises(LedgerError):
            historical_admission(c,authenticated_owner="owner_1",
                 reviewer="reviewer_1",consent_receipt="receipt:1",
                 source_integrity_verified=False)

    def test_explicit_admission_remains_historical_and_can_be_revoked(self):
        c=sample()
        admitted=historical_admission(c,authenticated_owner="owner_1",
            reviewer="reviewer_1",consent_receipt="receipt:1",
            source_integrity_verified=True)
        self.assertEqual(admitted.disposition,Disposition.ADMITTED_HISTORICAL)
        self.assertEqual(admitted.evidence_status,"historical_unverified")
        removed=revoke_historical(c,admitted,authenticated_owner="owner_1",
            reviewer="reviewer_1",reason="Consent withdrawn")
        self.assertEqual(removed.disposition,Disposition.REVOKED)
        self.assertEqual(removed.prior_decision_key,admitted.decision_key)
        with self.assertRaises(LedgerError):
            revoke_historical(c,admitted,authenticated_owner="other",
                reviewer="reviewer_1",reason="Bad owner")

    def test_idempotent_source_and_digest_binding(self):
        a=sample()
        b=sample()
        c=sample(message_id="message-2")
        self.assertEqual(a.candidate_key,b.candidate_key)
        self.assertNotEqual(a.candidate_key,c.candidate_key)
        self.assertEqual(triage(a).decision_key,triage(b).decision_key)

    def test_source_cannot_claim_currentness(self):
        with self.assertRaises(LedgerError):
            sample(temporal_status="verified_current")

    def test_invalid_identifiers_and_hashes_rejected(self):
        with self.assertRaises(LedgerError):
            sample(source_id="../../secret file")
        with self.assertRaises(LedgerError):
            sample(sha256="bad")

    def test_absence_of_model_instruction_authority(self):
        c=sample()
        result=triage(c)
        self.assertNotIn("system",str(result.disposition).lower())
        self.assertFalse(hasattr(c,"instruction"))

if __name__=="__main__":unittest.main()
