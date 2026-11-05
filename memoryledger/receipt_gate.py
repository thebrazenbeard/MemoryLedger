"""Pure, fail-closed STM -> historical-custody receipt reconciliation.

This is not an authority provider, memory writer, revoker, or deletion tool.
It cannot authenticate the verifier callback: a trusted host must inject one.
No transcript text, source locator, credentials, or private records are stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Callable

from .contracts import _id, _instant


_HEX = frozenset("0123456789abcdef")


def _digest(value: str, label: str) -> None:
    if type(value) is not str or len(value) != 64 or any(c not in _HEX for c in value):
        raise ValueError(f"invalid {label}")


class ReceiptStatus(StrEnum):
    HOLD = "HOLD"
    HISTORICAL_REVIEW_ONLY = "HISTORICAL_REVIEW_ONLY"
    PENDING_REVOCATION_ACKS = "PENDING_REVOCATION_ACKS"
    ACKS_VERIFIED_REVIEW_ONLY = "ACKS_VERIFIED_REVIEW_ONLY"


@dataclass(frozen=True, slots=True)
class SourceCustody:
    tenant_id: str
    owner_id: str
    agent_id: str
    source_id: str
    source_version_digest: str
    privacy_scope: str
    source_scope: str  # GLOBAL, PROJECT_BOUND, or UNKNOWN; never infer from title.
    native_project_id: str | None
    native_project_id_verified: bool
    recorded_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        for field in ("tenant_id", "owner_id", "agent_id", "source_id", "privacy_scope"):
            _id(getattr(self, field), field)
        _digest(self.source_version_digest, "source_version_digest")
        if self.source_scope not in ("GLOBAL", "PROJECT_BOUND", "UNKNOWN"):
            raise ValueError("invalid source_scope")
        if self.native_project_id is not None:
            _id(self.native_project_id, "native_project_id")
        if type(self.native_project_id_verified) is not bool:
            raise ValueError("native_project_id_verified must be bool")
        _instant(self.recorded_at, "recorded_at")
        _instant(self.expires_at, "expires_at")
        if self.expires_at <= self.recorded_at:
            raise ValueError("source expiry must follow recording")


@dataclass(frozen=True, slots=True)
class HistoricalReceipt:
    """DMS-like receipt. Caller strings alone never authenticate the receipt."""

    destination_id: str
    source_version_digest: str
    idempotency_key: str
    external_record_id: str
    receipt_mac: str

    def __post_init__(self) -> None:
        for name in ("destination_id", "external_record_id"):
            _id(getattr(self, name), name)
        for name in ("source_version_digest", "idempotency_key", "receipt_mac"):
            _digest(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class RevocationAck:
    """Opaque host-signed proof proposal for a DMS erase/revoke tombstone."""

    destination_id: str
    source_version_digest: str
    operation: str
    receipt_mac: str

    def __post_init__(self) -> None:
        _id(self.destination_id, "destination_id")
        _digest(self.source_version_digest, "source_version_digest")
        _digest(self.receipt_mac, "receipt_mac")
        if self.operation not in ("ERASE_SOURCE", "REVOKE_SCOPE"):
            raise ValueError("invalid revocation operation")


@dataclass(frozen=True, slots=True)
class ReceiptDecision:
    status: ReceiptStatus
    reason: str
    acknowledged: int = 0
    required: int = 0
    effect: str = "PROPOSAL_ONLY_NO_STORE_OR_MEMORY_EFFECT"


HistoricalVerifier = Callable[[SourceCustody, HistoricalReceipt], bool]
RevocationVerifier = Callable[[SourceCustody, RevocationAck], bool]


def _source_hold(source: SourceCustody, at: datetime) -> str | None:
    if source.source_scope == "UNKNOWN":
        return "SOURCE_SCOPE_UNRESOLVED"
    if source.source_scope == "PROJECT_BOUND" and (
        source.native_project_id is None or not source.native_project_id_verified
    ):
        return "NATIVE_PROJECT_ID_UNVERIFIED"
    if source.source_scope == "GLOBAL" and (
        source.native_project_id is not None or source.native_project_id_verified
    ):
        return "GLOBAL_SOURCE_WITH_UNEXPECTED_PROJECT_CLAIM"
    if at < source.recorded_at:
        return "SOURCE_NOT_YET_RECORDED"
    if at >= source.expires_at:
        return "SOURCE_NOT_CURRENT_FOR_HANDOFF"
    return None


def plan_historical_handoff(
    source: SourceCustody,
    receipt: HistoricalReceipt | None,
    *,
    destination_id: str,
    expected_idempotency_key: str,
    at: datetime,
    verifier: HistoricalVerifier | None = None,
) -> ReceiptDecision:
    """Only nominate authenticated historical evidence for further review.

    A result is *never* durable-current admission, nor proof a model read it.
    The host must independently own source custody, idempotency, and verifier.
    """
    if type(source) is not SourceCustody:
        raise TypeError("source must be SourceCustody")
    _id(destination_id, "destination_id")
    _digest(expected_idempotency_key, "expected_idempotency_key")
    _instant(at, "at")
    issue = _source_hold(source, at)
    if issue:
        return ReceiptDecision(ReceiptStatus.HOLD, issue)
    if type(receipt) is not HistoricalReceipt:
        return ReceiptDecision(ReceiptStatus.HOLD, "RECEIPT_REQUIRED")
    if (receipt.destination_id != destination_id
            or receipt.source_version_digest != source.source_version_digest
            or receipt.idempotency_key != expected_idempotency_key):
        return ReceiptDecision(ReceiptStatus.HOLD, "RECEIPT_BINDING_MISMATCH")
    if verifier is None:
        return ReceiptDecision(ReceiptStatus.HOLD, "INDEPENDENT_VERIFIER_REQUIRED")
    try:
        authentic = verifier(source, receipt)
    except Exception:
        authentic = False
    if authentic is not True:
        return ReceiptDecision(ReceiptStatus.HOLD, "HOST_RECEIPT_VERIFICATION_FAILED")
    return ReceiptDecision(
        ReceiptStatus.HISTORICAL_REVIEW_ONLY,
        "VERIFIED_CUSTODY_REQUIRES_SEPARATE_MEMORY_ADMISSION_REVIEW",
    )


def plan_revocation_reconciliation(
    source: SourceCustody,
    *,
    destinations: tuple[str, ...],
    acknowledgements: tuple[RevocationAck, ...],
    at: datetime,
    expected_operation: str = "ERASE_SOURCE",
    verifier: RevocationVerifier | None = None,
) -> ReceiptDecision:
    """Reconcile per-destination tombstone ACKs; never execute deletion.

    The caller's destination inventory is not authenticated here. Hosts must
    bind it to their original custody registry before this is meaningful.
    """
    if type(source) is not SourceCustody or type(destinations) is not tuple or type(acknowledgements) is not tuple:
        raise TypeError("exact source, destination tuple and acknowledgement tuple required")
    _instant(at, "at")
    if expected_operation not in ("ERASE_SOURCE", "REVOKE_SCOPE"):
        raise ValueError("invalid expected_operation")
    if not 1 <= len(destinations) <= 64:
        raise ValueError("destination list must be nonempty and bounded")
    for destination in destinations:
        _id(destination, "destination")
    if len(destinations) != len(set(destinations)):
        raise ValueError("duplicate destination in custody inventory")
    if len(acknowledgements) > 64 or any(type(a) is not RevocationAck for a in acknowledgements):
        raise ValueError("invalid acknowledgement snapshot")
    # Revocation has different admission semantics: a stale/unknown native
    # Project binding must NOT orphan an already-stored historical copy.
    # The trusted host verifier still owns actual scope/authorization checks.
    if at < source.recorded_at:
        return ReceiptDecision(ReceiptStatus.HOLD, "SOURCE_NOT_YET_RECORDED", required=len(destinations))
    # Expired or unclassified sources may still require erasure.
    seen: set[str] = set()
    verified = 0
    for ack in acknowledgements:
        if ack.destination_id not in destinations or ack.destination_id in seen:
            return ReceiptDecision(ReceiptStatus.HOLD, "ACK_TARGET_UNEXPECTED_OR_DUPLICATE", required=len(destinations))
        seen.add(ack.destination_id)
        if ack.source_version_digest != source.source_version_digest:
            return ReceiptDecision(ReceiptStatus.HOLD, "ACK_SOURCE_DIGEST_MISMATCH", required=len(destinations))
        if ack.operation != expected_operation:
            return ReceiptDecision(ReceiptStatus.HOLD, "ACK_OPERATION_MISMATCH", required=len(destinations))
        if verifier is None:
            return ReceiptDecision(ReceiptStatus.HOLD, "INDEPENDENT_VERIFIER_REQUIRED", required=len(destinations))
        try:
            authentic = verifier(source, ack)
        except Exception:
            authentic = False
        if authentic is not True:
            return ReceiptDecision(ReceiptStatus.HOLD, "HOST_ACK_VERIFICATION_FAILED", required=len(destinations))
        verified += 1
    if verified != len(destinations):
        return ReceiptDecision(ReceiptStatus.PENDING_REVOCATION_ACKS,
                               "AWAITING_DESTINATION_TOMBSTONE_ACKS", verified, len(destinations))
    return ReceiptDecision(ReceiptStatus.ACKS_VERIFIED_REVIEW_ONLY,
                           "HOST_MUST_VERIFY_CUSTODY_COMPLETENESS_AND_APPLY_POLICY", verified, len(destinations))
