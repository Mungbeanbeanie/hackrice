## Status: Staged
Target: `backend/app/accounts/verification.py` (Phase 8, item 5) — generate + verify codes, hashed at rest

- Resolves the flag raised during `db.py`'s review: codes are hashed (SHA-256) before ever reaching `store.py`/the DB — `verification_codes.code` never holds the raw code, only its hash. Comparison still works because hashing is deterministic; `store.consume_verification_code` compares hash-to-hash, unaware it's a hash.
- Small supporting edit to `backend/app/config.py`: add `VERIFICATION_CODE_TTL_MINUTES = int(os.getenv("VERIFICATION_CODE_TTL_MINUTES", "10"))` — consistent with existing precedent of env-tunable business constants (`SVD_RANK`, the tier thresholds, etc.)
- `CODE_LENGTH = 6` module constant (not config-tunable — a format decision, not an ops knob)
- `_generate_code() -> str`: `f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"` — uses `secrets`, not `random`, since this is a security-sensitive OTP
- `_hash_code(code: str) -> str`: `hashlib.sha256(code.encode()).hexdigest()`
- `request_code(email: str) -> str`:
  - `code = _generate_code()`
  - `expires_at = datetime.now(UTC) + timedelta(minutes=config.VERIFICATION_CODE_TTL_MINUTES)`
  - `store.store_verification_code(email, _hash_code(code), expires_at)`
  - returns the **raw** `code` — caller (`routes/auth.py`, later) passes it to `mailer.py` to actually send; this file never sends email itself, matching the file's plan.md-scoped responsibility
- `verify_code(email: str, code: str) -> bool`: `return store.consume_verification_code(email, _hash_code(code))` — hash the submitted code, delegate the stored-value/expiry/single-use check to `store.py`, which already owns that logic
- Imports: `hashlib`, `secrets`, `datetime.{datetime, timedelta, UTC}`, `app.config`, `app.accounts.store`
- No brute-force/attempt-limiting here either (same flag as before, still not in scope) — `verify_code` can be called repeatedly until the code expires
