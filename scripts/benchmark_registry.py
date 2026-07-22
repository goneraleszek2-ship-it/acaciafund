#!/usr/bin/env python3
"""Benchmark comparing JSON vs SQLite registry performance."""

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.registry_store import JsonRegistryStore, SqliteRegistryStore


def bench_load(store, label: str, iterations: int = 5) -> float:
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        store.load()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg = sum(times) / len(times)
    print(f"  {label:12s} load: {avg*1000:.1f}ms avg  (min={min(times)*1000:.1f}ms  max={max(times)*1000:.1f}ms)")
    return avg


def bench_get_item(store, slugs: list[str], iterations: int = 5) -> float:
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        for slug in slugs:
            store.get_item(slug)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg = sum(times) / len(times)
    n = len(slugs)
    per_lookup = avg / n * 1000
    print(f"  get_item ({n}x): {avg*1000:.1f}ms avg  ({per_lookup:.3f}ms/lookup)")
    return avg


def bench_get_items_filtered(store, iterations: int = 5) -> float:
    times = []
    pillars = ["aml", "stock", "data-engineering"]
    content_types = ["research", "learn", "knowledge"]
    for _ in range(iterations):
        start = time.perf_counter()
        for p in pillars:
            for ct in content_types:
                store.get_items(pillar=p, content_type=ct)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg = sum(times) / len(times)
    combos = len(pillars) * len(content_types)
    print(f"  get_items_filtered ({combos}x): {avg*1000:.1f}ms avg  ({avg/combos*1000:.3f}ms/query)")
    return avg


def bench_save(store, items_sample: list[dict], reg_template: dict, iterations: int = 5) -> float:
    times = []
    for _ in range(iterations):
        test_reg = {**reg_template, "content": items_sample}
        start = time.perf_counter()
        store.save(test_reg)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg = sum(times) / len(times)
    print(f"  save ({len(items_sample)} items): {avg*1000:.1f}ms avg  ({avg/len(items_sample)*1000:.3f}ms/item)")
    return avg


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark JSON vs SQLite registry performance."
    )
    parser.add_argument("--registry", default="registry.json", help="JSON registry path")
    parser.add_argument("--db", default="registry.db", help="SQLite database path")
    parser.add_argument("--iterations", type=int, default=5, help="Number of test iterations")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    db_path = Path(args.db)

    if not registry_path.exists():
        print(f"Error: {registry_path} not found")
        return

    print("Preparing stores...")
    json_store = JsonRegistryStore(registry_path)
    sqlite_store = SqliteRegistryStore(db_path)

    reg = json_store.load()
    items = reg.get("content", [])
    print(f"  Registry has {len(items)} items")

    slugs = [item["slug"] for item in items if "slug" in item]
    sample_slugs = random.sample(slugs, min(100, len(slugs)))

    sample_items = items[:100]

    reg_template = {k: v for k, v in reg.items() if k != "content"}

    print(f"\nBenchmarking ({args.iterations} iterations each)...\n")

    print("--- load ---")
    j_load = bench_load(json_store, "JSON", args.iterations)
    s_load = bench_load(sqlite_store, "SQLite", args.iterations)

    print()
    print("--- get_item (100 random lookups) ---")
    j_gitem = bench_get_item(json_store, sample_slugs, args.iterations)
    s_gitem = bench_get_item(sqlite_store, sample_slugs, args.iterations)

    print()
    print("--- get_items_filtered (pillar + content_type, 9 combos) ---")
    j_gif = bench_get_items_filtered(json_store, args.iterations)
    s_gif = bench_get_items_filtered(sqlite_store, args.iterations)

    print()
    print("--- save (100 items) ---")
    j_save = bench_save(json_store, sample_items, reg_template, args.iterations)
    s_save = bench_save(sqlite_store, sample_items, reg_template, args.iterations)

    print()
    print("=" * 60)
    print(f"{'Operation':<25} {'JSON (ms)':<15} {'SQLite (ms)':<15} {'Speedup':<10}")
    print("=" * 60)

    rows = [
        ("load", j_load * 1000, s_load * 1000),
        ("get_item x100", j_gitem * 1000, s_gitem * 1000),
        ("get_items_filtered x9", j_gif * 1000, s_gif * 1000),
        ("save x100", j_save * 1000, s_save * 1000),
    ]

    for name, jt, st in rows:
        ratio = jt / st if st > 0 else float("inf")
        winner = "SQLite" if ratio > 1 else "JSON"
        print(f"{name:<25} {jt:<15.1f} {st:<15.1f} {ratio:<7.1f}x ({winner})")


if __name__ == "__main__":
    main()
