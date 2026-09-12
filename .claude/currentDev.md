## Status: Staged
Target: `backend/app/models.py` (Phase 8, item 2) — add `Account` schema

- Add `from datetime import datetime` import
- Add `class Account(BaseModel): id: str; email: str; created_at: datetime` — placed after `ComparisonResult` at the end of the file
- `email` is plain `str`, not `pydantic.EmailStr` — avoids adding the `email-validator` extra dependency just for this; format validation (if any) belongs at the API boundary in `routes/auth.py` (not built yet), consistent with how `SearchQuery.raw_input` is also plain `str` with validation/inference logic living in the route rather than the model
- No other changes to `models.py` — `SearchMode`, `SearchQuery`, `SpecAttribute`, `Product`, `Tier`, `ComparisonResult` untouched
