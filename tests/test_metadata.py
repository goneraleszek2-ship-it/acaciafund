from pathlib import Path


def test_story_and_run_manifests():
    from core.metadata import build_run_manifest, build_story_manifest

    story = build_story_manifest(
        content_id="2026-05-22-aml",
        pillar="aml",
        title="Sample AML synthesis",
        date="2026-05-22",
        source_urls=["https://example.com/a"],
        story_count=3,
        signals={"avg_sqi": 0.5},
        bloom_levels=["remember", "understand"],
        questions_count=2,
        flashcards_count=4,
        assets=[],
        lineage={"run_id": "20260522T000000Z"},
        quality_flags=[],
    )
    assert story["manifest_type"] == "story"
    assert story["checksum"]

    run = build_run_manifest(
        run_id="20260522T000000Z",
        started_at="2026-05-22T00:00:00Z",
        ended_at="2026-05-22T00:01:00Z",
        source_counts={"hn": 10, "arxiv": 2},
        generated_pages=[{"pillar": "aml", "path": "content/pl/blog/2026-05-22-aml/index.md"}],
        output_count=1,
        notes=[],
    )
    assert run["manifest_type"] == "run"
    assert run["checksum"]


def test_asset_manifest(tmp_path, monkeypatch):
    from core import metadata

    repo_root = tmp_path / "repo"
    asset_path = repo_root / "content" / "pl" / "blog" / "demo" / "thumb.svg"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_text("<svg />", encoding="utf-8")

    monkeypatch.setattr(metadata, "BASE_DIR", repo_root)

    manifest = metadata.build_asset_manifest(
        content_id="demo",
        asset_type="thumbnail",
        path=asset_path,
        source_url="https://example.com/story",
    )

    assert manifest["manifest_type"] == "asset"
    assert manifest["path"].startswith("content/pl/blog/demo/")
    assert manifest["checksum"]


def test_registry_index_and_lookup(tmp_path, monkeypatch):
    from core import metadata

    repo_root = tmp_path / "repo"
    blog_root = repo_root / "content" / "pl" / "blog"
    run_root = repo_root / "registry" / "runs"
    blog_root.mkdir(parents=True, exist_ok=True)
    run_root.mkdir(parents=True, exist_ok=True)

    story_aml = metadata.build_story_manifest(
        content_id="2026-05-22-aml",
        pillar="aml",
        title="AML synthesis",
        date="2026-05-22",
        source_urls=["https://example.com/a"],
        story_count=4,
        signals={"avg_sqi": 0.4},
        bloom_levels=["remember"],
        questions_count=1,
        flashcards_count=2,
        assets=[],
        lineage={"run_id": "20260522T010000Z"},
        quality_flags=[],
    )
    story_stock = metadata.build_story_manifest(
        content_id="2026-05-22-stock",
        pillar="stock",
        title="Markets synthesis",
        date="2026-05-22",
        source_urls=["https://example.com/b"],
        story_count=5,
        signals={"avg_sqi": 0.6},
        bloom_levels=["understand"],
        questions_count=2,
        flashcards_count=3,
        assets=[],
        lineage={"run_id": "20260522T010000Z"},
        quality_flags=[],
    )
    metadata.write_json(blog_root / "2026-05-22-aml" / "manifest.json", story_aml)
    metadata.write_json(blog_root / "2026-05-22-stock" / "manifest.json", story_stock)

    run_manifest = metadata.build_run_manifest(
        run_id="20260522T010000Z",
        started_at="2026-05-22T01:00:00Z",
        ended_at="2026-05-22T01:05:00Z",
        source_counts={"hn": 12, "arxiv": 2},
        generated_pages=[
            {"pillar": "aml", "path": "content/pl/blog/2026-05-22-aml/index.md"},
            {"pillar": "stock", "path": "content/pl/blog/2026-05-22-stock/index.md"},
        ],
        output_count=2,
        notes=[],
    )
    metadata.write_json(run_root / "20260522T010000Z.json", run_manifest)

    monkeypatch.setattr(metadata, "BASE_DIR", repo_root)
    monkeypatch.setattr(metadata, "REGISTRY_DIR", repo_root / "registry")
    monkeypatch.setattr(metadata, "RUNS_DIR", run_root)
    monkeypatch.setattr(metadata, "SCHEMA_DIR", Path(__file__).resolve().parents[1] / "schemas")

    index = metadata.build_registry_index()
    assert index["manifest_type"] == "registry-index"
    assert index["counts"]["pages"] == 2
    assert index["counts"]["runs"] == 1
    assert index["latest_by_pillar"]["aml"] == "2026-05-22-aml"

    index_path = metadata.write_registry_index()
    assert index_path.exists()

    loaded = metadata.load_registry_index()
    assert loaded["latest_run_id"] == "20260522T010000Z"
    assert metadata.get_story_manifest("2026-05-22-stock")["pillar"] == "stock"
    assert metadata.get_latest_story_manifest("aml")["content_id"] == "2026-05-22-aml"
    assert metadata.get_run_manifest("20260522T010000Z")["output_count"] == 2
