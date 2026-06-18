"""
AcaciaFund Ontology Transform
Maintains technology ontology and concept relationships.
"""

import polars as pl
from datetime import datetime, timezone
from transforms.api import transform, Input, Output, LightweightInput, LightweightOutput
from myproject.config import DatasetPaths


@transform.using(
    output=Output(DatasetPaths.ONTOLOGY_CONCEPTS),
    sources=Input(DatasetPaths.CLEANED_DATA),
)
def compute(
    sources: LightweightInput,
    output: Output
) -> None:
    """
    Extract concepts from articles and build ontology.
    """
    df = sources.polars(lazy=True)
    
    df_concepts = df.select([
        pl.col("tags").explode().alias("concept_name"),
    ]).unique()
    
    df_pillars = pl.DataFrame({
        "concept_name": ["AML", "Markets", "Data Engineering"],
    })
    
    df_concepts = pl.concat([
        df_pillars.with_columns([
            pl.lit("pillar").alias("concept_type"),
            pl.lit("").alias("parent_concept_id"),
            pl.lit([]).alias("child_concepts"),
            pl.lit([]).alias("related_concepts"),
            pl.lit(1.0).alias("domain_coverage"),
        ]),
        df_concepts.with_columns([
            pl.lit("technology").alias("concept_type"),
            pl.lit("").alias("parent_concept_id"),
            pl.lit([]).alias("child_concepts"),
            pl.lit([]).alias("related_concepts"),
            pl.lit(0.0).alias("domain_coverage"),
        ]),
    ])
    
    df_concepts = df_concepts.with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("last_updated"),
    ])
    
    output.write_table(df_concepts)


@transform.using(
    output=Output(DatasetPaths.ONTOLOGY_RELATIONSHIPS),
    sources=Input(DatasetPaths.CLEANED_DATA),
)
def relationships(
    sources: LightweightInput,
    output: Output
) -> None:
    """
    Extract concept relationships from co-occurrences.
    """
    df = sources.polars(lazy=True)
    
    df_pairs = df.select([
        pl.col("tags").alias("tags_list"),
    ]).filter(pl.col("tags").list.length() > 1)
    
    df_pairs = df_pairs.with_columns([
        pl.col("tags_list").explode().alias("tag1"),
        pl.col("tags_list").explode().alias("tag2"),
    ]).filter(pl.col("tag1") < pl.col("tag2"))
    
    df_pairs = df_pairs.select([
        pl.col("tag1").alias("source_concept"),
        pl.col("tag2").alias("target_concept"),
    ]).unique()
    
    df_pairs = df_pairs.with_columns([
        pl.lit("cooccurs_with").alias("relationship_type"),
        pl.lit(0.5).alias("strength"),
        pl.lit(datetime.now(timezone.utc)).alias("created_at"),
    ])
    
    output.write_table(df_pairs)
