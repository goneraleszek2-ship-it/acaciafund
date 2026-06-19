"""
AcaciaFund Ontology Transform
Maintains technology ontology and concept relationships.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput


@transform.using(
    output=Output("ontology_concepts"),
    sources=Input("acacia_portal_clean_data"),
)
def compute(
    sources: LightweightInput,
    output: Output
) -> None:
    """
    Extract concepts from articles and build ontology.
    """
    df = sources.pandas()
    
    all_tags = []
    for tags in df["tags"]:
        if isinstance(tags, list):
            all_tags.extend(tags)
        else:
            all_tags.append(tags)
    
    df_concepts = pd.DataFrame({"concept_name": list(set(all_tags))})
    
    df_pillars = pd.DataFrame({
        "concept_name": ["AML", "Markets", "Data Engineering"],
    })
    df_pillars["concept_type"] = "pillar"
    df_pillars["parent_concept_id"] = ""
    df_pillars["child_concepts"] = ""
    df_pillars["related_concepts"] = ""
    df_pillars["domain_coverage"] = 1.0
    
    df_concepts["concept_type"] = "technology"
    df_concepts["parent_concept_id"] = ""
    df_concepts["child_concepts"] = ""
    df_concepts["related_concepts"] = ""
    df_concepts["domain_coverage"] = 0.0
    
    df_concepts = pd.concat([df_pillars, df_concepts], ignore_index=True)
    
    df_concepts["last_updated"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df_concepts)


@transform.using(
    output=Output("ontology_relationships"),
    sources=Input("acacia_portal_clean_data"),
)
def relationships(
    sources: LightweightInput,
    output: Output
) -> None:
    """
    Extract concept relationships from co-occurrences.
    """
    df = sources.pandas()
    
    pairs = []
    for tags in df["tags"]:
        if isinstance(tags, list) and len(tags) > 1:
            for i in range(len(tags)):
                for j in range(i + 1, len(tags)):
                    pairs.append((tags[i], tags[j]))
    
    df_pairs = pd.DataFrame(pairs, columns=["tag1", "tag2"])
    df_pairs = df_pairs[df_pairs["tag1"] < df_pairs["tag2"]].drop_duplicates()
    df_pairs.columns = ["source_concept", "target_concept"]
    
    df_pairs["relationship_type"] = "cooccurs_with"
    df_pairs["strength"] = 0.5
    df_pairs["created_at"] = datetime.now(timezone.utc)
    
    output.write_dataframe(df_pairs)
