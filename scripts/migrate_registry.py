#!/usr/bin/env python3
"""CLI script to migrate registry between JSON and SQLite backends."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.registry_store import JsonRegistryStore, RegistryStoreFactory, SqliteRegistryStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate registry between JSON and SQLite backends."
    )
    parser.add_argument("--to", choices=["json", "sqlite"], help="Target backend")
    parser.add_argument(
        "--registry",
        default="registry.json",
        help="JSON registry path (default: registry.json)",
    )
    parser.add_argument(
        "--db", default="registry.db", help="SQLite database path (default: registry.db)"
    )
    parser.add_argument("--verify", action="store_true", help="Compare source and target counts")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--verbose", action="store_true", help="Show progress")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    db_path = Path(args.db)

    if args.verify:
        json_store = JsonRegistryStore(registry_path) if registry_path.exists() else None
        sqlite_store = SqliteRegistryStore(db_path) if db_path.exists() else None
        if json_store:
            jcount = json_store.count()
            jitems = len(json_store.load().get("content", []))
            print(f"JSON  ({registry_path}): {jcount} items ({jitems} total)")
        else:
            print(f"JSON  ({registry_path}): not found")
            jcount = 0
        if sqlite_store and db_path.exists():
            scount = sqlite_store.count()
            sitems = len(sqlite_store.load().get("content", []))
            print(f"SQLite ({db_path}): {scount} items ({sitems} total)")
        else:
            print(f"SQLite ({db_path}): not found")
            scount = 0
        if jcount == scount and jcount > 0:
            print("PASS: counts match")
        elif jcount > 0 and scount > 0:
            print(f"FAIL: counts differ (JSON={jcount}, SQLite={scount})")
        else:
            print("INFO: one or both stores unavailable")
        return

    if not args.to:
        parser.error("Specify --to json or --to sqlite (or use --verify)")

    if args.to == "sqlite":
        if not registry_path.exists():
            print(f"Error: {registry_path} not found")
            sys.exit(1)
        source = JsonRegistryStore(registry_path)
        target = SqliteRegistryStore(db_path)
        src_name = f"JSON ({registry_path})"
        tgt_name = f"SQLite ({db_path})"
    else:
        if not db_path.exists():
            print(f"Error: {db_path} not found")
            sys.exit(1)
        source = SqliteRegistryStore(db_path)
        target = JsonRegistryStore(registry_path)
        src_name = f"SQLite ({db_path})"
        tgt_name = f"JSON ({registry_path})"

    if args.dry_run:
        reg = source.load()
        items = reg.get("content", [])
        print(f"Dry run: would migrate {len(items)} items")
        print(f"  Source: {src_name}")
        print(f"  Target: {tgt_name}")
        return

    stats = RegistryStoreFactory.migrate(
        source, target, batch_size=100, verbose=args.verbose or True
    )
    print(f"Migrated {stats['items']} items in {stats['elapsed_s']}s")
    print(f"  Source: {stats['source_type']}")
    print(f"  Target: {stats['target_type']}")


if __name__ == "__main__":
    main()
