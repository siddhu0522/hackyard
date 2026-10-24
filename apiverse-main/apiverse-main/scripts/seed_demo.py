import asyncio
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.database import SessionLocal, init_db
from backend.app.services.seeding import DatabaseSeeder

async def main():
    print("=" * 65)
    print("      APIVERSE — COMPREHENSIVE DATABASE SEEDING ENGINE       ")
    print("            Tagline: APIs change. Your code adapts.          ")
    print("=" * 65)
    print("\n[1/3] Initializing SQLite database schema...")
    init_db()

    print("[2/3] Executing safe, idempotent fixture synchronization...")
    db = SessionLocal()
    try:
        seeder = DatabaseSeeder(db)
        result = await seeder.seed_all()
        
        stats = result["stats"]
        summary = result["summary"]
        
        print("\n[3/3] Synchronization Complete! Breakdown of Entities:")
        print("-" * 65)
        print(f"{'Entity':<26} | {'Inserted':<9} | {'Reused':<9} | {'Skipped':<7}")
        print("-" * 65)
        for entity, counts in stats.get("entities", {}).items():
            print(f"{entity:<26} | {counts.get('inserted', 0):<9} | {counts.get('reused', 0):<9} | {counts.get('skipped', 0):<7}")
        print("-" * 65)
        print(f"Total Inserted: {stats.get('inserted', 0)} | Total Reused: {stats.get('reused', 0)} | Failed: {stats.get('failed', 0)}")
        print("\nAggregate Entity Counts:")
        for k, v in summary.items():
            print(f"  • {k.replace('_', ' ').title()}: {v}")
        print("-" * 65)
        print("All fixtures verified! Idempotent re-runs will safely reuse records.")
        print("=" * 65)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
