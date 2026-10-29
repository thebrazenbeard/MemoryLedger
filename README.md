# MemoryLedger — candidate review contract

MemoryLedger is Vera's **conversation-to-memory decision boundary**. It sits between preserved ChatGPT/Drive evidence and governed STM/DeepMemoryStorage adoption. It does not store private transcripts in GitHub, train neural weights, or promote historical records into current authority.

The stdlib-only `candidate_ledger.py` provides immutable provenance-bound `Candidate` and `Decision` records plus `triage`, `historical_admission`, and `revoke_historical`. Unknown or true `is_do_not_remember` flags and non-user/assistant roles are quarantined. Even eligible records require authenticated owner identity, independently verified source integrity, an explicit reviewer and consent receipt; approval grants **historical evidence** status only. Record hashes provide deterministic idempotence; revocations link to prior decisions.

```powershell
py -3 -m unittest -v test_candidate_ledger
```

This is a **source-only candidate** for `chat_history_ingestion_live_coordination`. For real persistence, use a separately provisioned owner-private encrypted store with durable append-only receipts, scoped access, retention and correction/revocation propagation. Do not print private source IDs or text to public logs. Do not treat archived source statements as current user identity or live Lantern currentness.
