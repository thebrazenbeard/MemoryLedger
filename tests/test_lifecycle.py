"""Synthetic-only public contract checks. No private material or external effects."""
import dataclasses
import hashlib
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from memoryledger import (
    ConversationEvent, HostAuthorization, LifecyclePlanner, LifecyclePolicy,
    Purpose, SpeechAct, Disposition, CandidateIndex,
)

UTC = timezone.utc
NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
HASH = hashlib.sha256(b"SYNTHETIC_A").hexdigest()


def event(**changes):
    fields = dict(
        event_id="event-1", tenant_id="tenant-A", project_id="project-A",
        identity_id="vera-A", conversation_id="conversation-A", speaker="user",
        occurred_at=NOW - timedelta(days=1), content_sha256=HASH,
        source_ref="synthetic:origin-1", privacy_scope="private-A",
        speech_act=SpeechAct.ASSERTION, corrects_event_id=None,
    )
    fields.update(changes)
    return ConversationEvent(**fields)


def grant(**changes):
    fields = dict(
        principal="human-A", tenant_id="tenant-A", project_id="project-A",
        identity_id="vera-A", conversation_id="conversation-A",
        privacy_scopes=("private-A",),
        purposes=(Purpose.WORKING, Purpose.CURRENT_REVIEW, Purpose.HISTORICAL_REVIEW, Purpose.CORRECTION_REVIEW),
        consent_ref="synthetic-consent-A", issued_at=NOW-timedelta(hours=1),
        expires_at=NOW+timedelta(hours=1), revoked=False,
    )
    fields.update(changes)
    return HostAuthorization(**fields)


def planner(authorization=None, policy=None):
    return LifecyclePlanner(
        authorizer=authorization if authorization is not None else (lambda e, now: grant()),
        policy=policy if policy is not None else LifecyclePolicy(
            historical_review_after=timedelta(days=30), source_expiry_after=timedelta(days=45)),
    )


class ContractTests(unittest.TestCase):
    def test_no_host_authorizer_fails_closed(self):
        result = LifecyclePlanner(policy=LifecyclePolicy()).propose(event(), at=NOW)
        self.assertEqual(result.disposition, Disposition.HOLD)
        self.assertEqual(result.reason, "HOST_AUTHENTICATION_REQUIRED")

    def test_assertion_can_only_propose_review_not_admit(self):
        result = planner().propose(event(), at=NOW)
        self.assertEqual(result.disposition, Disposition.REVIEW_CURRENT)
        self.assertEqual(result.claim_ceiling, "PROPOSAL_ONLY_NO_MEMORY_ADMISSION_OR_EFFECT")
        self.assertFalse(hasattr(result, "effect_receipt"))
        self.assertNotIn("SYNTHETIC_A", repr(result))

    def test_non_user_assertions_never_propose_current_memory_review(self):
        # A user's host grant cannot be silently inherited by an assistant or
        # tool utterance from the same conversation.  Those statements may be
        # recorded as historical evidence, never current owner facts by default.
        for speaker in ("assistant", "system", "developer", "tool", "unknown"):
            with self.subTest(speaker=speaker):
                result = planner().propose(event(speaker=speaker), at=NOW)
                self.assertNotEqual(result.disposition, Disposition.REVIEW_CURRENT)
                self.assertEqual(result.disposition, Disposition.WORKING_ONLY)

    def test_assistant_assertion_can_still_be_historical_evidence(self):
        result = planner().propose(
            event(speaker="assistant", occurred_at=NOW - timedelta(days=30)), at=NOW,
        )
        self.assertEqual(result.disposition, Disposition.REVIEW_HISTORICAL)
        self.assertEqual(result.claim_ceiling, "PROPOSAL_ONLY_NO_MEMORY_ADMISSION_OR_EFFECT")

    def test_historical_review_at_day_30_is_not_export(self):
        result = planner().propose(event(occurred_at=NOW-timedelta(days=30)), at=NOW)
        self.assertEqual(result.disposition, Disposition.REVIEW_HISTORICAL)
        self.assertEqual(result.reason, "HISTORICAL_REVIEW_ELIGIBLE_NOT_EXPORTED")

    def test_day_45_expiration_precedes_all_review(self):
        result = planner().propose(event(occurred_at=NOW-timedelta(days=45)), at=NOW)
        self.assertEqual(result.disposition, Disposition.EXPIRE)
        self.assertEqual(result.reason, "SOURCE_EXPIRED_NOT_EXPORTABLE")

    def test_no_global_policy_implied(self):
        result = planner(policy=LifecyclePolicy()).propose(event(occurred_at=NOW-timedelta(days=90)), at=NOW)
        self.assertEqual(result.disposition, Disposition.REVIEW_CURRENT)

    def test_quote_hypothetical_question_joke_instruction_never_current_review(self):
        for speech_act in (SpeechAct.QUOTE, SpeechAct.HYPOTHETICAL, SpeechAct.QUESTION,
                           SpeechAct.JOKE, SpeechAct.INSTRUCTION, SpeechAct.UNKNOWN):
            with self.subTest(act=speech_act):
                result=planner().propose(event(speech_act=speech_act),at=NOW)
                self.assertEqual(result.disposition, Disposition.WORKING_ONLY)

    def test_analyzer_claim_cannot_self_authorize(self):
        result = LifecyclePlanner(policy=LifecyclePolicy()).propose(event(speech_act=SpeechAct.ASSERTION),at=NOW)
        self.assertEqual(result.disposition, Disposition.HOLD)

    def test_cross_project_identity_tenant_and_conversation_are_rejected(self):
        for changed in (dict(project_id="project-B"),dict(identity_id="vera-B"),
                        dict(tenant_id="tenant-B"),dict(conversation_id="conversation-B")):
            with self.subTest(changed=changed):
                result=planner().propose(event(**changed),at=NOW)
                self.assertEqual(result.disposition,Disposition.HOLD)
                self.assertEqual(result.reason,"HOST_SCOPE_MISMATCH")

    def test_privacy_scope_is_checked_before_review(self):
        result=planner().propose(event(privacy_scope="private-B"),at=NOW)
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"PRIVACY_SCOPE_NOT_GRANTED")

    def test_expired_future_issued_and_revoked_host_grants_fail_closed(self):
        for bad in (grant(expires_at=NOW),grant(issued_at=NOW+timedelta(seconds=1)),
                    grant(revoked=True)):
            with self.subTest(grant=bad):
                result=planner(authorization=lambda e,at,bad=bad: bad).propose(event(),at=NOW)
                self.assertEqual(result.disposition,Disposition.HOLD)

    def test_host_callback_exceptions_fail_closed(self):
        def fail(e,at):raise RuntimeError("provider offline")
        result=planner(authorization=fail).propose(event(),at=NOW)
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"HOST_AUTHENTICATION_REQUIRED")

    def test_cross_identity_correction_blocked(self):
        candidate=event(event_id="old-1",privacy_scope="private-B")
        correction=event(event_id="new-1",speech_act=SpeechAct.CORRECTION,corrects_event_id="old-1")
        result=planner().propose(correction,at=NOW,index=CandidateIndex((candidate,)))
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"CORRECTION_SCOPE_MISMATCH")

    def test_correction_cannot_restart_expired_target_retention(self):
        previous=event(event_id="old-1",occurred_at=NOW-timedelta(days=46))
        change=event(event_id="new-1",speech_act=SpeechAct.CORRECTION,corrects_event_id="old-1")
        result=planner().propose(change,at=NOW,index=CandidateIndex((previous,)))
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"CORRECTION_TARGET_EXPIRED")

    def test_correction_cannot_claim_target_from_future(self):
        previous=event(event_id="old-1",occurred_at=NOW)
        change=event(event_id="new-1",occurred_at=NOW-timedelta(days=1),speech_act=SpeechAct.CORRECTION,corrects_event_id="old-1")
        result=planner().propose(change,at=NOW,index=CandidateIndex((previous,)))
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"CORRECTION_TEMPORAL_CONFLICT")

    def test_correction_cycle_is_not_a_reviewable_history(self):
        previous=event(event_id="old-1",speech_act=SpeechAct.CORRECTION,
                       corrects_event_id="new-1",occurred_at=NOW-timedelta(days=2))
        change=event(event_id="new-1",speech_act=SpeechAct.CORRECTION,
                     corrects_event_id="old-1")
        result=planner().propose(change,at=NOW,index=CandidateIndex((previous,)))
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"CORRECTION_CYCLE")

    def test_unknown_correction_target_never_mutates_record(self):
        result=planner().propose(event(speech_act=SpeechAct.CORRECTION,corrects_event_id="missing"),at=NOW)
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"CORRECTION_TARGET_UNVERIFIED")

    def test_matching_correction_review_only(self):
        previous=event(event_id="old-1")
        change=event(event_id="new-1",speech_act=SpeechAct.CORRECTION,corrects_event_id="old-1")
        result=planner().propose(change,at=NOW,index=CandidateIndex((previous,)))
        self.assertEqual(result.disposition,Disposition.REVIEW_CORRECTION)
        self.assertEqual(result.target_event_id,"old-1")

    def test_idempotent_replay_is_not_a_new_proposal(self):
        prior=event()
        result=planner().propose(prior,at=NOW,index=CandidateIndex((prior,)))
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"ALREADY_OBSERVED")

    def test_same_id_different_digest_conflict(self):
        old=event()
        new=event(content_sha256=hashlib.sha256(b"synthetic-other").hexdigest())
        result=planner().propose(new,at=NOW,index=CandidateIndex((old,)))
        self.assertEqual(result.disposition,Disposition.REJECT)
        self.assertEqual(result.reason,"SOURCE_ID_COLLISION")

    def test_same_id_but_different_identity_is_collision(self):
        old=event(identity_id="vera-B")
        result=planner().propose(event(),at=NOW,index=CandidateIndex((old,)))
        self.assertEqual(result.disposition,Disposition.REJECT)

    def test_unauthorized_historical_review_never_falls_back_to_export(self):
        restricted=grant(purposes=(Purpose.WORKING,))
        result=planner(authorization=lambda e,at:restricted).propose(event(occurred_at=NOW-timedelta(days=30)),at=NOW)
        self.assertEqual(result.disposition,Disposition.WORKING_ONLY)

    def test_future_event_is_held_not_rewritten(self):
        result=planner().propose(event(occurred_at=NOW+timedelta(days=1)),at=NOW)
        self.assertEqual(result.disposition,Disposition.HOLD)
        self.assertEqual(result.reason,"FUTURE_EVENT_TIME")

    def test_naive_timestamp_invalid(self):
        with self.assertRaises(ValueError):event(occurred_at=datetime(2026,10,1))

    def test_invalid_identity_and_source_digest_invalid(self):
        for change in (dict(project_id=""),dict(event_id="../escape"),dict(content_sha256="invalid")):
            with self.subTest(change=change),self.assertRaises(ValueError):event(**change)

    def test_mutable_scope_and_authorization_rejected(self):
        with self.assertRaises((ValueError,TypeError)):
            grant(privacy_scopes=["private-A"])

    def test_review_result_carries_no_raw_content_or_private_locator(self):
        e=event(source_ref="synthetic:secret-locator")
        result=planner().propose(e,at=NOW)
        self.assertFalse(hasattr(result,"source_ref"))
        self.assertFalse(hasattr(result,"raw_text"))
        self.assertNotIn("secret-locator",repr(result))

    def test_pure_planning_does_not_invoke_filesystem_database_or_network(self):
        with patch("builtins.open",side_effect=AssertionError("file I/O")), \
             patch("sqlite3.connect",side_effect=AssertionError("database I/O")), \
             patch("socket.socket",side_effect=AssertionError("network I/O")):
            result=planner().propose(event(),at=NOW)
        self.assertEqual(result.disposition,Disposition.REVIEW_CURRENT)

    def test_unbounded_candidate_index_rejected(self):
        with self.assertRaises(ValueError):
            CandidateIndex(tuple(event(event_id=f"synthetic-{n}") for n in range(1025)))

    def test_ambiguous_duplicate_ids_in_index_rejected(self):
        with self.assertRaises(ValueError):
            CandidateIndex((event(event_id="synthetic-1"),event(event_id="synthetic-1")))

    def test_unexpected_host_grant_type_fails_closed(self):
        result=planner(authorization=lambda e,at:{"allow":True}).propose(event(),at=NOW)
        self.assertEqual(result.disposition,Disposition.HOLD)

    def test_bad_policy_window_rejected(self):
        with self.assertRaises(ValueError):
            LifecyclePolicy(historical_review_after=timedelta(days=50),source_expiry_after=timedelta(days=45))


class CorrectionChainAdversarialTests(unittest.TestCase):
    def test_three_node_cycle_is_held(self):
        a=event(event_id="node-A",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-C")
        b=event(event_id="node-B",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-A")
        c=event(event_id="node-C",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-B")
        result=planner().propose(c,at=NOW,index=CandidateIndex((a,b)))
        self.assertEqual((result.disposition,result.reason),(Disposition.HOLD,"CORRECTION_CYCLE"))

    def test_self_correction_is_held_as_cycle(self):
        c=event(event_id="self",speech_act=SpeechAct.CORRECTION,corrects_event_id="self")
        result=planner().propose(c,at=NOW)
        self.assertEqual((result.disposition,result.reason),(Disposition.HOLD,"CORRECTION_CYCLE"))

    def test_missing_transitive_ancestor_is_held(self):
        b=event(event_id="node-B",speech_act=SpeechAct.CORRECTION,corrects_event_id="missing")
        c=event(event_id="node-C",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-B")
        result=planner().propose(c,at=NOW,index=CandidateIndex((b,)))
        self.assertEqual((result.disposition,result.reason),(Disposition.HOLD,"CORRECTION_TARGET_UNVERIFIED"))

    def test_transitive_identity_scope_is_checked(self):
        a=event(event_id="node-A",identity_id="vera-other")
        b=event(event_id="node-B",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-A")
        c=event(event_id="node-C",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-B")
        result=planner().propose(c,at=NOW,index=CandidateIndex((a,b)))
        self.assertEqual((result.disposition,result.reason),(Disposition.HOLD,"CORRECTION_SCOPE_MISMATCH"))

    def test_transitive_age_and_time_are_checked(self):
        a=event(event_id="node-A",occurred_at=NOW-timedelta(days=46))
        b=event(event_id="node-B",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-A")
        c=event(event_id="node-C",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-B")
        result=planner().propose(c,at=NOW,index=CandidateIndex((a,b)))
        self.assertEqual((result.disposition,result.reason),(Disposition.HOLD,"CORRECTION_TARGET_EXPIRED"))

    def test_acyclic_three_node_chain_remains_reviewable(self):
        a=event(event_id="node-A",occurred_at=NOW-timedelta(days=3))
        b=event(event_id="node-B",occurred_at=NOW-timedelta(days=2),
                speech_act=SpeechAct.CORRECTION,corrects_event_id="node-A")
        c=event(event_id="node-C",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-B")
        result=planner().propose(c,at=NOW,index=CandidateIndex((a,b)))
        self.assertEqual(result.disposition,Disposition.REVIEW_CORRECTION)
        self.assertEqual(result.target_event_id,"node-B")

    def test_chain_traversal_budget_fail_closed(self):
        a=event(event_id="node-0",occurred_at=NOW-timedelta(days=2))
        nodes=[a]
        for i in range(1,66):
            nodes.append(event(event_id=f"node-{i}",occurred_at=NOW-timedelta(days=1),
                               speech_act=SpeechAct.CORRECTION,corrects_event_id=f"node-{i-1}"))
        c=event(event_id="node-new",speech_act=SpeechAct.CORRECTION,corrects_event_id="node-65")
        result=planner().propose(c,at=NOW,index=CandidateIndex(tuple(nodes)))
        self.assertEqual((result.disposition,result.reason),(Disposition.HOLD,"CORRECTION_CHAIN_BUDGET_EXCEEDED"))

if __name__=="__main__":unittest.main()
