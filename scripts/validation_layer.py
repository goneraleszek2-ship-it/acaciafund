#!/usr/bin/env python3
"""
validation_layer.py
-------------------
Compares the local derived ontology (concepts & relationships) with the
live Foundry ontology (object types & link types). Emits a delta report
and a Pipeline Health JSON blob.

Additionally monitors the master ontology schema checksum stored in
registry.json to detect drift.
"""

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
DIST_DIR = PROJECT_ROOT / "dist"
BACKUP_DIR = PROJECT_ROOT / "backup"
MASTER_SCHEMA_PATH = BACKUP_DIR / "master_ontology_schema.json"

# Foundry connection (reuse helpers from foundry_integration.py)
FOUNDRY_HOST = os.environ.get("FOUNDRY_HOST", "tierpalan.euw-3.palantirfoundry.co.uk")
FOUNDRY_TOKEN = os.environ.get("FOUNDRY_TOKEN")


# ----------------------------------------------------------------------
# Helper: Foundry client (minimal)
# ----------------------------------------------------------------------
def _get_foundry_client():
    from foundry_dev_tools import Config, FoundryContext, JWTTokenProvider

    if not FOUNDRY_TOKEN:
        raise RuntimeError("FOUNDRY_TOKEN environment variable not set")
    token_provider = JWTTokenProvider(host=FOUNDRY_HOST, jwt=FOUNDRY_TOKEN)
    return FoundryContext(Config(), token_provider=token_provider)


# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
def file_sha256(path: Path) -> str:
    """Return SHA-256 hex digest of a file."""
    hash_sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def load_local_ontology():
    concepts_path = DIST_DIR / "foundry_ontology_concepts.parquet"
    rels_path = DIST_DIR / "foundry_ontology_relationships.parquet"
    if not concepts_path.exists() or not rels_path.exists():
        raise FileNotFoundError(
            "Local ontology Parquet files missing. Run the ontology workflow first."
        )
    concepts = pd.read_parquet(concepts_path)
    relationships = pd.read_parquet(rels_path)
    concept_dicts = concepts.to_dict(orient="records")
    rel_dicts = relationships.to_dict(orient="records")
    return concept_dicts, rel_dicts


def fetch_live_ontology(ctx):
    ont_client = ctx.ontologies
    ont_list = ont_client.list()
    if not ont_list:
        raise RuntimeError("No ontologies found in Foundry")
    ont_rid = ont_list[0]["rid"]

    def _get(path):
        resp = ont_client.api_request("GET", path)
        if hasattr(resp, "status_code") and resp.status_code != 200:
            raise RuntimeError(f"Foundry API error {resp.status_code}: {resp.text}")
        return resp.json() if hasattr(resp, "json") else resp

    # Object types
    obj_path = f"/v1/ontology/{ont_rid}/object-types"
    obj_resp = _get(obj_path)
    live_objects = obj_resp.get("data", [])

    # Link types
    link_path = f"/v1/ontology/{ont_rid}/link-types"
    link_resp = _get(link_path)
    live_links = link_resp.get("data", [])

    # Normalise
    live_obj_dicts = [
        {
            "apiName": o.get("apiName"),
            "rid": o.get("rid"),
            "description": o.get("description"),
            "primaryKey": o.get("primaryKey"),
            "properties": o.get("properties", []),
        }
        for o in live_objects
    ]
    live_link_dicts = [
        {
            "apiName": link.get("apiName"),
            "rid": link.get("rid"),
            "description": link.get("description"),
            "subjectType": link.get("subjectType"),
            "objectType": link.get("objectType"),
            "cardinality": link.get("cardinality"),
            "properties": link.get("properties", []),
        }
        for link in live_links
    ]
    return live_obj_dicts, live_link_dicts, ont_rid


def _diff_sets(local_keys, live_keys, label):
    only_local = local_keys - live_keys
    only_live = live_keys - local_keys
    return {
        "label": label,
        "only_local": sorted(only_local),
        "only_live": sorted(only_live),
        "in_sync": len(only_local) == 0 and len(only_live) == 0,
    }


def diff_ontology(local_objects, local_links, live_objects, live_links):
    local_obj_names = {o["apiName"] for o in local_objects}
    live_obj_names = {o["apiName"] for o in live_objects}
    obj_diff = _diff_sets(local_obj_names, live_obj_names, "object_types")

    local_link_names = {link["apiName"] for link in local_links}
    live_link_names = {link["apiName"] for link in live_links}
    link_diff = _diff_sets(local_link_names, live_link_names, "link_types")

    return {
        "object_types": obj_diff,
        "link_types": link_diff,
        "overall_in_sync": obj_diff["in_sync"] and link_diff["in_sync"],
    }


def _check_token_expiry(token):
    try:
        import base64
        import json as _json

        parts = token.split(".")
        if len(parts) != 3:
            return None, None
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        claims = _json.loads(decoded)
        exp = claims.get("exp")
        if exp:
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            time_left = exp_dt - now
            return exp_dt, time_left.total_seconds()
    except Exception:
        pass
    return None, None


def pipeline_health():
    health = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": {},
        "warnings": [],
        "errors": [],
    }
    start = time.time()
    try:
        ctx = _get_foundry_client()
        health["steps"]["foundry_connect"] = {
            "status": "ok",
            "latency_ms": round((time.time() - start) * 1000, 2),
        }
    except Exception as e:
        health["steps"]["foundry_connect"] = {"status": "error", "error": str(e)}
        health["errors"].append(f"Foundry connection failed: {e}")
        return health

    # Load local ontology
    t0 = time.time()
    try:
        local_objs, local_links = load_local_ontology()
        health["steps"]["load_local"] = {
            "status": "ok",
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "object_count": len(local_objs),
            "link_count": len(local_links),
        }
    except Exception as e:
        health["steps"]["load_local"] = {"status": "error", "error": str(e)}
        health["errors"].append(f"Failed to load local ontology: {e}")
        return health

    # Fetch live ontology
    t1 = time.time()
    try:
        live_objs, live_links, ont_rid = fetch_live_ontology(ctx)
        health["steps"]["fetch_live"] = {
            "status": "ok",
            "latency_ms": round((time.time() - t1) * 1000, 2),
            "ontology_rid": ont_rid,
            "object_count": len(live_objs),
            "link_count": len(live_links),
        }
    except Exception as e:
        health["steps"]["fetch_live"] = {"status": "error", "error": str(e)}
        health["errors"].append(f"Failed to fetch live ontology: {e}")
        return health

    # Diff
    t2 = time.time()
    try:
        diff = diff_ontology(local_objs, local_links, live_objs, live_links)
        health["steps"]["diff"] = {
            "status": "ok",
            "latency_ms": round((time.time() - t2) * 1000, 2),
            "in_sync": diff["overall_in_sync"],
            "details": diff,
        }
        if not diff["overall_in_sync"]:
            health["warnings"].append("Ontology drift detected between local and Foundry.")
    except Exception as e:
        health["steps"]["diff"] = {"status": "error", "error": str(e)}
        health["errors"].append(f"Diff failed: {e}")

    # Checksum validation for master ontology schema
    t3 = time.time()
    try:
        if MASTER_SCHEMA_PATH.exists():
            current_hash = file_sha256(MASTER_SCHEMA_PATH)
            # Load registry to see stored checksum
            if REGISTRY_PATH.exists():
                with REGISTRY_PATH.open("r") as f:
                    registry = json.load(f)
                stored_hash = registry.get("masterOntologyChecksum")
                if stored_hash is None:
                    health["warnings"].append(
                        "masterOntologyChecksum not present in registry.json; storing current hash."
                    )
                    # Optionally update registry
                    registry["masterOntologyChecksum"] = current_hash
                    with REGISTRY_PATH.open("w") as f:
                        json.dump(registry, f, indent=2)
                elif stored_hash != current_hash:
                    health["errors"].append(
                        "Critical Drift: master ontology schema checksum mismatch!"
                    )
                    health["warnings"].append(
                        "Consider updating registry.json with the new checksum."
                    )
                else:
                    health["steps"]["checksum"] = {
                        "status": "ok",
                        "latency_ms": round((time.time() - t3) * 1000, 2),
                        "hash": current_hash,
                    }
            else:
                health["warnings"].append("registry.json not found; skipping checksum validation.")
        else:
            health["warnings"].append("master_ontology_schema.json not found.")
    except Exception as e:
        health["steps"]["checksum"] = {"status": "error", "error": str(e)}
        health["errors"].append(f"Checksum validation failed: {e}")

    # Token expiry warning (if JWT)
    exp_dt, secs_left = _check_token_expiry(FOUNDRY_TOKEN)
    if exp_dt and secs_left is not None:
        if secs_left < 1800:  # 30 minutes
            health["warnings"].append(
                f"Foundry token expires at {exp_dt.isoformat()} ({int(secs_left / 60)} min left)."
            )
    elif FOUNDRY_TOKEN:
        health["warnings"].append("Unable to parse token expiry (non-JWT or malformed).")

    # Overall status
    health["status"] = "ok" if not health["errors"] else "error"
    return health


def main():
    health = pipeline_health()
    print(json.dumps(health, indent=2))


if __name__ == "__main__":
    main()
