"""Deterministic proposals only: no destination writes, source reads or effects."""
from __future__ import annotations

from datetime import datetime
from typing import Callable

from .contracts import (
    CandidateIndex, ConversationEvent, Disposition, HostAuthorization,
    LifecyclePolicy, LifecycleProposal, Purpose, SpeechAct, _instant,
)


class LifecyclePlanner:
    """Advisory-only planning over bounded, host-provided evidence.

    The host must own the authorizer, event index, clock and policy. They are
    *not* authenticated by construction of these Python objects. In particular,
    passing a model-controlled callable as `authorizer` defeats the trust model.
    No sink, mutable database, model adapter or tool execution exists here.
    """

    def __init__(
        self,
        *,
        authorizer: Callable[[ConversationEvent, datetime], HostAuthorization | None] | None = None,
        policy: LifecyclePolicy,
    ):
        if type(policy) is not LifecyclePolicy:
            raise TypeError("policy must be LifecyclePolicy")
        if authorizer is not None and not callable(authorizer):
            raise TypeError("authorizer must be an injected callable")
        self._authorizer = authorizer
        self._policy = policy

    def propose(
        self, event: ConversationEvent, *, at: datetime,
        index: CandidateIndex = CandidateIndex(),
    ) -> LifecycleProposal:
        if type(event) is not ConversationEvent or type(index) is not CandidateIndex:
            raise TypeError("event and index must be exact contracts")
        _instant(at, "at")

        def make(disposition: Disposition, reason: str, *, target: str | None = None) -> LifecycleProposal:
            return LifecycleProposal(event.event_id, event.content_sha256, disposition, reason,
                                     target_event_id=target)

        # Re-evaluate host-granted authority at each proposal; the value itself
        # is an assertion from the injected trusted boundary, not a credential.
        authorization = None
        if self._authorizer is not None:
            try:
                authorization = self._authorizer(event, at)
            except Exception:
                authorization = None
        if type(authorization) is not HostAuthorization:
            return make(Disposition.HOLD, "HOST_AUTHENTICATION_REQUIRED")

        if any(getattr(authorization, field) != getattr(event, field)
               for field in ("tenant_id", "project_id", "identity_id", "conversation_id")):
            return make(Disposition.HOLD, "HOST_SCOPE_MISMATCH")
        if event.privacy_scope not in authorization.privacy_scopes:
            return make(Disposition.HOLD, "PRIVACY_SCOPE_NOT_GRANTED")
        if authorization.revoked or not (authorization.issued_at <= at < authorization.expires_at):
            return make(Disposition.HOLD, "CONSENT_NOT_CURRENT")
        if at < event.occurred_at:
            return make(Disposition.HOLD, "FUTURE_EVENT_TIME")

        # The index is not itself authoritative; it must come from the host's
        # scope-checked view. Refuse ambiguous IDs instead of choosing a row.
        matches = [prior for prior in index.events if prior.event_id == event.event_id]
        if matches:
            if len(matches) == 1 and matches[0] == event:
                return make(Disposition.HOLD, "ALREADY_OBSERVED")
            return make(Disposition.REJECT, "SOURCE_ID_COLLISION")

        age = at - event.occurred_at
        if self._policy.source_expiry_after is not None and age >= self._policy.source_expiry_after:
            return make(Disposition.EXPIRE, "SOURCE_EXPIRED_NOT_EXPORTABLE")

        allowed = authorization.purposes
        if event.speech_act is SpeechAct.CORRECTION:
            # Only a trusted host may supply a complete, scope-constrained index.
            # Traverse the whole ancestor chain: a direct 2-node comparison
            # misses longer cycles and corrupted or expired source ancestors.
            by_id = {prior.event_id: prior for prior in index.events}
            visited = {event.event_id}
            target_id = event.corrects_event_id
            child = event
            steps = 0
            fields = ("tenant_id", "project_id", "identity_id", "conversation_id", "privacy_scope")
            while target_id is not None:
                if target_id in visited:
                    return make(Disposition.HOLD, "CORRECTION_CYCLE")
                if steps >= 64:
                    return make(Disposition.HOLD, "CORRECTION_CHAIN_BUDGET_EXCEEDED")
                previous = by_id.get(target_id)
                if previous is None:
                    return make(Disposition.HOLD, "CORRECTION_TARGET_UNVERIFIED")
                if any(getattr(previous, f) != getattr(event, f) for f in fields):
                    return make(Disposition.HOLD, "CORRECTION_SCOPE_MISMATCH")
                if previous.occurred_at > child.occurred_at:
                    return make(Disposition.HOLD, "CORRECTION_TEMPORAL_CONFLICT")
                if (self._policy.source_expiry_after is not None
                        and at - previous.occurred_at >= self._policy.source_expiry_after):
                    return make(Disposition.HOLD, "CORRECTION_TARGET_EXPIRED")
                visited.add(target_id)
                steps += 1
                child = previous
                target_id = (previous.corrects_event_id
                             if previous.speech_act is SpeechAct.CORRECTION else None)
            if Purpose.CORRECTION_REVIEW not in allowed:
                return make(Disposition.HOLD, "CORRECTION_REVIEW_NOT_GRANTED")
            return make(Disposition.REVIEW_CORRECTION, "CORRECTION_REQUIRES_INDEPENDENT_REVIEW",
                        target=event.corrects_event_id)

        if event.speech_act is SpeechAct.ASSERTION:
            if (self._policy.historical_review_after is not None
                    and age >= self._policy.historical_review_after
                    and Purpose.HISTORICAL_REVIEW in allowed):
                return make(Disposition.REVIEW_HISTORICAL, "HISTORICAL_REVIEW_ELIGIBLE_NOT_EXPORTED")
            # The host's grant to review current owner claims does not turn
            # assistant, system, developer or tool output into a user claim.
            # Those utterances remain historical/working evidence unless a
            # future explicit source-role authority contract is qualified.
            if event.speaker == "user" and Purpose.CURRENT_REVIEW in allowed:
                return make(Disposition.REVIEW_CURRENT, "CURRENT_ADMISSION_REVIEW_ONLY")

        if Purpose.WORKING in allowed:
            return make(Disposition.WORKING_ONLY, "WORKING_CONTEXT_ONLY_UNTRUSTED")
        return make(Disposition.HOLD, "NO_APPLICABLE_PURPOSE_GRANT")
