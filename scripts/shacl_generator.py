"""SHACL Schema Generator: Generate SHACL shape files from ontology for Edge validation."""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/root/acaciafund")
ONTOLOGY_PATH = ROOT / "data" / "ontology.json"
SHACL_OUTPUT = ROOT / "static" / "shacl" / "shapes.ttl"


def generate_shacl_shapes(ontology_path: Path = None, output_path: Path = None) -> str:
    """Generate SHACL shape definitions from ontology concepts and relations.

    SHACL (Shapes Constraint Language) defines validation rules for RDF data.
    This generates shape definitions for deontic concepts (O, P, F).
    """
    if ontology_path is None:
        ontology_path = ONTOLOGY_PATH
    if output_path is None:
        output_path = SHACL_OUTPUT

    with open(ontology_path) as f:
        data = json.load(f)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ttl_lines = []

    # Prefix definitions
    ttl_lines.append("@prefix sh: <http://www.w3.org/ns/shacl#> .")
    ttl_lines.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    ttl_lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    ttl_lines.append("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
    ttl_lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    ttl_lines.append("")

    # Generate SHACL shapes for each pillar's deontic concepts
    pillars = ["aml", "stock", "data-engineering"]

    for pillar in pillars:
        ttl_lines.append(f"# Deontic shapes for pillar: {pillar}")
        ttl_lines.append(f":{pillar}DeonticShapes a sh:Shape ;")

        # Concept concepts for this pillar
        concepts = [c for c in data["concepts"] if c.get("pillar") == pillar]
        ttl_lines.append(f"    sh:targetClass owl:Thing ;")

        # Generate shape constraints based on deontic classification
        obligations = [c for c in concepts if classify_deontic(c) == "O"]
        permissions = [c for c in concepts if classify_deontic(c) == "P"]
        prohibitions = [c for c in concepts if classify_deontic(c) == "F"]

        if obligations:
            ttl_lines.append(f"    # Obligation constraints")
            ttl_lines.append(f"    sh:annotatedProperty owl:Obligation ;")
            for concept in obligations[:3]:  # Limit to first 3 for brevity
                cid = concept["id"]
                ttl_lines.append(f"    sh:includes <{cid}> ;")
            if len(obligations) > 3:
                ttl_lines.append(f"    # ... plus {len(obligations) - 3} more obligation concepts")

        if permissions:
            ttl_lines.append(f"    # Permission constraints")
            ttl_lines.append(f"    sh:annotatedProperty owl:Permission ;")
            for concept in permissions[:3]:
                cid = concept["id"]
                ttl_lines.append(f"    sh:includes <{cid}> ;")
            if len(permissions) > 3:
                ttl_lines.append(f"    # ... plus {len(permissions) - 3} more permission concepts")

        if prohibitions:
            ttl_lines.append(f"    # Prohibition constraints")
            ttl_lines.append(f"    sh:annotatedProperty owl:Prohibition ;")
            for concept in prohibitions[:3]:
                cid = concept["id"]
                ttl_lines.append(f"    sh:includes <{cid}> ;")
            if len(prohibitions) > 3:
                ttl_lines.append(f"    # ... plus {len(prohibitions) - 3} more prohibition concepts")

        ttl_lines.append("")

    # Write the Turtle file
    with open(output_path, "w") as f:
        f.write("\n".join(ttl_lines))

    return str(output_path)


def classify_deontic(concept: dict) -> str:
    """Classify a concept into deontic state O, P, or F."""
    pillar = concept.get("pillar", "")
    epistemic = concept.get("epistemic_status", "").lower()
    if epistemic in ["regulatory", "constitutive"] and pillar in ["aml", "compliance"]:
        return "O"
    elif epistemic in ["instrumental", "pragmatic"] and pillar in ["stock", "market"]:
        return "P"
    elif epistemic == "ontological":
        return "F"
    return "N"


def main(argv: list = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="SHACL Schema Generator")
    parser.add_argument("--ontology", required=True, help="Path to ontology JSON")
    parser.add_argument("--output", required=True, help="Path to output SHACL TTL file")
    args = parser.parse_args(argv) if argv else parser.parse_args()

    output_path = Path(args.output)
    result = generate_shacl_shapes(Path(args.ontology), output_path)

    print(f"SHACL shapes generated: {output_path}")
    print(f"Shapes cover pillars: aml, stock, data-engineering")
    return 0


if __name__ == "__main__":
    sys.exit(main())
