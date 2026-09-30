"""Migrate legacy Streamlit history into the modern MySQL history table.

The legacy Streamlit app stored per-user history as text strings in
data/users.json. This script reads every top-level user that has a "history"
array and inserts each record into the transcriptions table.

By default the legacy username is looked up verbatim in the MySQL users table.
Legacy accounts that no longer exist can be assigned to an existing MySQL user
via the USER_MAP below (legacy name -> modern MySQL username).

These legacy records are text-only: they have no stored audio file, so playback
and re-transcription will be unavailable for them, but they will appear in the
History page just like any other transcription entry.

The script is idempotent. It computes a fingerprint from the owner user_id,
the text and the original timestamp, and skips any record already imported.
Re-running it will never create duplicates.

Usage:
    venv\\Scripts\\python.exe scripts\\migrate_legacy_history.py [--dry-run]
"""

import argparse
import asyncio
import hashlib
import json
import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

USER_FILE = os.path.join(ROOT, "data", "users.json")

# Map legacy usernames (from data/users.json) to modern MySQL usernames that
# should own their history. Used when the legacy account no longer exists.
USER_MAP = {
    "Adeola1": "Admin",
}


def fingerprint(user_id: int, text: str, timestamp: str) -> str:
    # Normalize the timestamp to whole seconds matching how MySQL stores a
    # DATETIME column: it ROUNDS microseconds to the nearest second (e.g.
    # 13:23:21.693 -> 13:23:22). The legacy input and the stored row must be
    # normalized the same way or duplicate detection would never match.
    normalized = ""
    ts = parse_timestamp(timestamp)
    if ts is not None:
        if ts.microsecond >= 500_000:
            ts = ts.replace(microsecond=0)
            from datetime import timedelta
            ts += timedelta(seconds=1)
        else:
            ts = ts.replace(microsecond=0)
        normalized = ts.strftime("%Y-%m-%d %H:%M:%S")
    return hashlib.sha256(
        f"{user_id}\x00{text}\x00{normalized}".encode("utf-8")
    ).hexdigest()


def parse_timestamp(value):
    if not value:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def load_legacy_history():
    """Return a list of (username, records) for every top-level user with history."""
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = []
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(value.get("history"), list):
            records = [r for r in value["history"] if (r.get("text") or "").strip()]
            if records:
                out.append((key, records))
    return out


async def run(dry_run: bool):
    from sqlalchemy import select
    import database
    import models.user  # noqa: F401  (register mappers with related models)
    import models.transcription  # noqa: F401
    import models.correction  # noqa: F401  (User relationship target)
    import models.audit_log  # noqa: F401
    from models.user import User
    from models.transcription import Transcription

    legacy = load_legacy_history()
    if not legacy:
        print("No legacy history found in data/users.json.")
        return

    stats = {"no_user": 0, "duplicate": 0, "inserted": 0}

    async with database.async_session() as db:
        for legacy_username, records in legacy:
            mapped_username = USER_MAP.get(legacy_username, legacy_username)
            user_res = await db.execute(
                select(User.id).where(User.username == mapped_username)
            )
            user = user_res.scalar_one_or_none()
            if not user:
                if mapped_username == legacy_username:
                    print(
                        f"[WARN] No MySQL user named '{legacy_username}' found. "
                        f"Skipping {len(records)} legacy record(s)."
                    )
                else:
                    print(
                        f"[WARN] Legacy user '{legacy_username}' maps to "
                        f"'{mapped_username}', but no such MySQL user exists. "
                        f"Skipping {len(records)} legacy record(s)."
                    )
                stats["no_user"] += len(records)
                continue

            existing_fps = set()
            full_res = await db.execute(
                select(Transcription).where(Transcription.user_id == user)
            )
            for rec in full_res.scalars():
                ts = rec.created_at.isoformat() if rec.created_at else ""
                existing_fps.add(fingerprint(user, rec.final_text or "", ts))

            imported_here = 0
            skipped_here = 0
            for rec in records:
                text = rec["text"].strip()
                timestamp = rec.get("timestamp") or rec.get("date") or ""
                fp = fingerprint(user, text, timestamp)
                if fp in existing_fps:
                    skipped_here += 1
                    continue

                if dry_run:
                    print(f"  [dry-run] would import for '{legacy_username}': {text[:40]!r}")
                    continue

                row = Transcription(
                    user_id=user,
                    activity_type="transcription",
                    raw_text=text,
                    final_text=text,
                    source_language="yo",
                    engine="legacy",
                    created_at=parse_timestamp(timestamp),
                )
                db.add(row)
                imported_here += 1
                existing_fps.add(fp)

            stats["duplicate"] += skipped_here
            stats["inserted"] += imported_here

            if not dry_run and imported_here:
                print(
                    f"Imported {imported_here} record(s) for '{legacy_username}' "
                    f"(as '{mapped_username}' in MySQL; {skipped_here} duplicate(s) skipped)."
                )

        if not dry_run:
            await db.commit()

    await database.engine.dispose()

    print("\n=== Summary ===")
    print(f"Dry run:             {dry_run}")
    print(f"Imported:            {stats['inserted']}")
    print(f"Skipped (no user):   {stats['no_user']}")
    print(f"Skipped (duplicate): {stats['duplicate']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Do not write anything.")
    args = parser.parse_args()
    asyncio.run(run(args.dry_run))
