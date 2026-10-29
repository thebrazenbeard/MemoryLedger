"""Provenance-first candidate decisions for historical AI conversation memory.

Public SOURCE CONTRACT. Do not store private transcripts or memory rows in Git.
A candidate is evidence for review, never identity, tool authority or current truth.
"""
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

_ID = re.compile(r"[A-Za-z0-9_:.@/-]{2,256}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_ROLES = frozenset(("user", "assistant"))


class LedgerError(ValueError):
    pass


class Disposition(str, Enum):
    QUARANTINE = "QUARANTINE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ADMITTED_HISTORICAL = "ADMITTED_HISTORICAL"
    REVOKED = "REVOKED"


def _valid(value, field):
    if type(value) is not str or not _ID.fullmatch(value):
        raise LedgerError("invalid " + field)
    return value


@dataclass(frozen=True)
class Candidate:
    tenant: str
    owner: str
    source_id: str
    message_id: str
    author_role: str
    sha256: str
    source_scope: str
    remember_flag: bool | None
    source_kind: str = "chatgpt_account_export"
    temporal_status: str = "historical_unverified"

    def __post_init__(self):
        for name in ("tenant", "owner", "source_id", "message_id",
                     "source_scope", "source_kind"):
            _valid(getattr(self,name),name)
        if type(self.remember_flag) not in (bool,type(None)):
            raise LedgerError("invalid remember flag")
        if not _SHA.fullmatch(self.sha256):
            raise LedgerError("invalid source digest")
        if self.temporal_status != "historical_unverified":
            raise LedgerError("source cannot certify currentness")

    @property
    def candidate_key(self):
        payload=json.dumps((self.tenant,self.owner,self.source_kind,
                            self.source_id,self.message_id,self.sha256),
                           separators=(",",":")).encode()
        return hashlib.sha256(b"memory-ledger-candidate-v1\0"+payload).hexdigest()


@dataclass(frozen=True)
class Decision:
    candidate_key: str
    disposition: Disposition
    evidence_status: str
    reason: str
    reviewer: str | None = None
    prior_decision_key: str | None = None

    @property
    def decision_key(self):
        payload=json.dumps((self.candidate_key,self.disposition.value,
            self.evidence_status,self.reason,self.reviewer,self.prior_decision_key),
            separators=(",",":")).encode()
        return hashlib.sha256(b"memory-ledger-decision-v1\0"+payload).hexdigest()


def triage(candidate: Candidate) -> Decision:
    if not isinstance(candidate,Candidate):
        raise LedgerError("candidate required")
    if candidate.author_role not in _ROLES:
        return Decision(candidate.candidate_key,Disposition.QUARANTINE,
                        "historical_unverified","non-conversation role excluded")
    if candidate.remember_flag is not False:
        return Decision(candidate.candidate_key,Disposition.QUARANTINE,
                        "historical_unverified","source remember preference absent or denied")
    return Decision(candidate.candidate_key,Disposition.REVIEW_REQUIRED,
                    "historical_unverified","authorized review and current consent needed")


def historical_admission(candidate: Candidate, *,
                         authenticated_owner: str,
                         reviewer: str,
                         consent_receipt: str,
                         source_integrity_verified: bool) -> Decision:
    initial=triage(candidate)
    if initial.disposition is not Disposition.REVIEW_REQUIRED:
        raise LedgerError("source policy forbids admission")
    if type(authenticated_owner) is not str or authenticated_owner != candidate.owner:
        raise LedgerError("owner authorization missing")
    _valid(reviewer,"reviewer")
    _valid(consent_receipt,"consent receipt")
    if source_integrity_verified is not True:
        raise LedgerError("source integrity must be independently verified")
    return Decision(candidate.candidate_key,Disposition.ADMITTED_HISTORICAL,
                    "historical_unverified",
                    "explicit historical-only consent "+consent_receipt,
                    reviewer,initial.decision_key)


def revoke_historical(candidate: Candidate, previous: Decision, *,
                      authenticated_owner: str, reviewer: str, reason: str) -> Decision:
    if previous.candidate_key != candidate.candidate_key:
        raise LedgerError("wrong candidate")
    if previous.disposition is not Disposition.ADMITTED_HISTORICAL:
        raise LedgerError("only admitted history can be revoked")
    if authenticated_owner != candidate.owner:
        raise LedgerError("owner authorization missing")
    _valid(reviewer,"reviewer")
    if type(reason) is not str or not 1 <= len(reason) <= 400:
        raise LedgerError("explicit revocation reason required")
    return Decision(candidate.candidate_key,Disposition.REVOKED,
                    "historical_unverified",reason,reviewer,
                    previous.decision_key)
