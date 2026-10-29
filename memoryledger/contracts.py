"""Immutable, narrowly scoped contracts for an advisory-only memory lifecycle lab."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
import re

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_DIGEST = re.compile(r"[a-f0-9]{64}\Z")


def _id(value: str, label: str) -> None:
    if type(value) is not str or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"invalid {label}")


def _instant(value: datetime, label: str) -> None:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone aware")


class SpeechAct(StrEnum):
    ASSERTION = "ASSERTION"
    QUESTION = "QUESTION"
    HYPOTHETICAL = "HYPOTHETICAL"
    QUOTE = "QUOTE"
    JOKE = "JOKE"
    CORRECTION = "CORRECTION"
    INSTRUCTION = "INSTRUCTION"
    UNKNOWN = "UNKNOWN"


class Purpose(StrEnum):
    WORKING = "WORKING"
    CURRENT_REVIEW = "CURRENT_REVIEW"
    HISTORICAL_REVIEW = "HISTORICAL_REVIEW"
    CORRECTION_REVIEW = "CORRECTION_REVIEW"


class Disposition(StrEnum):
    HOLD = "HOLD"
    REJECT = "REJECT"
    EXPIRE = "EXPIRE"
    WORKING_ONLY = "WORKING_ONLY"
    REVIEW_CURRENT = "REVIEW_CURRENT"
    REVIEW_HISTORICAL = "REVIEW_HISTORICAL"
    REVIEW_CORRECTION = "REVIEW_CORRECTION"


@dataclass(frozen=True, slots=True)
class ConversationEvent:
    event_id: str
    tenant_id: str
    project_id: str
    identity_id: str
    conversation_id: str
    speaker: str
    occurred_at: datetime
    content_sha256: str
    source_ref: str
    privacy_scope: str
    speech_act: SpeechAct
    corrects_event_id: str | None = None

    def __post_init__(self) -> None:
        for key in ("event_id", "tenant_id", "project_id", "identity_id", "conversation_id", "speaker", "privacy_scope", "source_ref"):
            _id(getattr(self,key),key)
        _instant(self.occurred_at,"occurred_at")
        if type(self.content_sha256) is not str or not _DIGEST.fullmatch(self.content_sha256):
            raise ValueError("invalid content_sha256")
        if type(self.speech_act) is not SpeechAct:
            raise ValueError("speech_act must be exact")
        if self.corrects_event_id is not None:
            _id(self.corrects_event_id,"corrects_event_id")
        if self.speech_act is SpeechAct.CORRECTION and self.corrects_event_id is None:
            raise ValueError("correction requires target")
        if self.speech_act is not SpeechAct.CORRECTION and self.corrects_event_id is not None:
            raise ValueError("only correction may target event")


@dataclass(frozen=True, slots=True)
class HostAuthorization:
    """An assertion returned by an injected trusted host, not self-verifying proof."""
    principal: str
    tenant_id: str
    project_id: str
    identity_id: str
    conversation_id: str
    privacy_scopes: tuple[str, ...]
    purposes: tuple[Purpose, ...]
    consent_ref: str
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False

    def __post_init__(self) -> None:
        for key in ("principal", "tenant_id", "project_id", "identity_id", "conversation_id", "consent_ref"):
            _id(getattr(self,key),key)
        for key in ("issued_at", "expires_at"):
            _instant(getattr(self,key),key)
        if not (type(self.privacy_scopes) is tuple and all(type(x) is str and _IDENTIFIER.fullmatch(x) for x in self.privacy_scopes)):
            raise ValueError("privacy_scopes must be validated immutable identifiers")
        if not (type(self.purposes) is tuple and all(type(x) is Purpose for x in self.purposes)):
            raise ValueError("purposes must be validated immutable purposes")
        if type(self.revoked) is not bool:
            raise ValueError("revoked must be boolean")


@dataclass(frozen=True, slots=True)
class LifecyclePolicy:
    """Optional age windows supplied by the host; NOT global Vera retention policy."""
    historical_review_after: timedelta | None = None
    source_expiry_after: timedelta | None = None

    def __post_init__(self) -> None:
        for key in ("historical_review_after", "source_expiry_after"):
            value = getattr(self,key)
            if value is not None and (type(value) is not timedelta or value <= timedelta(0)):
                raise ValueError(f"invalid {key}")
        if (self.historical_review_after is not None and self.source_expiry_after is not None
                and self.historical_review_after >= self.source_expiry_after):
            raise ValueError("historical review must precede expiry")


@dataclass(frozen=True, slots=True)
class CandidateIndex:
    """Untrusted event snapshot. Does not prove storage admission or consent."""
    events: tuple[ConversationEvent, ...] = ()

    def __post_init__(self) -> None:
        if type(self.events) is not tuple or any(type(x) is not ConversationEvent for x in self.events):
            raise TypeError("events must be immutable ConversationEvent instances")
        if len(self.events) > 1024:
            raise ValueError("candidate index exceeds fixed 1024-event planning budget")
        ids = [value.event_id for value in self.events]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate index has ambiguous duplicate event identifiers")


@dataclass(frozen=True, slots=True)
class LifecycleProposal:
    event_id: str
    content_sha256: str
    disposition: Disposition
    reason: str
    target_event_id: str | None = None
    claim_ceiling: str = "PROPOSAL_ONLY_NO_MEMORY_ADMISSION_OR_EFFECT"
