"""
AcaciaFund Ontology Transform
Maintains technology ontology and concept relationships.
"""

import pandas as pd
from transforms.api import transform, Input, Output


@transform(
    clean_data=Input("acacia_portal_clean_data"),
    concepts_output=Output("ontology_concepts"),
)
def extract_concepts(clean_data, concepts_output):
    df = clean_data.pandas()

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

    concepts_output.write_dataframe(df_concepts)


@transform(
    clean_data=Input("acacia_portal_clean_data"),
    relationships_output=Output("ontology_relationships"),
)
def extract_relationships(clean_data, relationships_output):
    df = clean_data.pandas()

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

    relationships_output.write_dataframe(df_pairs)
