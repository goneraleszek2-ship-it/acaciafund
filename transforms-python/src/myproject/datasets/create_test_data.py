<<<<<<< HEAD
import polars as pl
from datetime import datetime, timezone
from transforms.api import transform_using, Input, O
@transform_using(
    # TODO: Replace this placeholder with the actual absolute path to your Foundry raw dataset
        # e.g., "/Company/Projects/Acacia/Data/raw_source_data"
            input_dataset=Input("SOURCE_DATASET_PATH"),
                output_dataset=Output("lacacia_portal_clean_data")
                )
                def clean_and_standardize(input_dataset, output_dataset) -> None:
                    """
                        Clean and standardize AcaciaFund portal data.
                            
                                This transform:
                                    - Validates input data schema
                                        - Handles missing and invalid values
                                            - Standardizes data formats
                                                - Applies business rules
                                                    - Generates quality metrics
                                                        """
                                                            try:
                                                                    # 1. Read input data as a Polars LazyFrame for optimized execution
                                                                            df = input_dataset.polars(lazy=True)
                                                                                    
                                                                                            # 2. Validate required columns
                                                                                                    required_columns = {"source_id", "title", "pillar", "is_active", "is_published"}
                                                                                                            current_columns = set(df.columns)
                                                                                                                    
                                                                                                                            missing_columns = required_columns - current_columns
                                                                                                                                    if missing_columns:
                                                                                                                                                raise ValueError(f"Missing required columns: {missing_columns}")
                                                                                                                                                            
                                                                                                                                                                    # 3. Data Quality Checks & Structural Inferences
                                                                                                                                                                            df = df.with_columns([
                                                                                                                                                                                        # Ensure source_id is not null and is valid
                                                                                                                                                                                                    pl.when(pl.col("source_id").is_null())
                                                                                                                                                                                                                .then(pl.lit(False))
                                                                                                                                                                                                                            .otherwise(pl.lit(True))
                                                                                                                                                                                                                                        .alias("source_id_valid"),
                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                # Ensure title is not null and is valid
                                                                                                                                                                                                                                                                            pl.when(pl.col("title").is_null())
                                                                                                                                                                                                                                                                                        .then(pl.lit(False))
                                                                                                                                                                                                                                                                                                    .otherwise(pl.lit(True))
                                                                                                                                                                                                                                                                                                                .alias("title_valid"),
                                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                        # Standardize title casing and strip whitespace
                                                                                                                                                                                                                                                                                                                                                    pl.col("title").str.strip_chars().str.to_uppercase().alias("title"),
                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                            # Standardize pillar values
                                                                                                                                                                                                                                                                                                                                                                                        pl.col("pillar").str.strip_chars().str.to_lowercase().alias("pillar")
                                                                                                                                                                                                                                                                                                                                                                                                ])
                                                                                                                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                                                                                                                                # 4. Apply business filtration rules
                                                                                                                                                                                                                                                                                                                                                                                                                        df = df.filter(
                                                                                                                                                                                                                                                                                                                                                                                                                                    (pl.col("is_active") == True) & 
                                                                                                                                                                                                                                                                                                                                                                                                                                                (pl.col("is_published") == True)
                                                                                                                                                                                                                                                                                                                                                                                                                                                        )
                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                        # 5. Calculate overall quality metrics and metadata tracking
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                df = df
=======
"""
AcaciaFund Test Data Source
Generates realistic test data for the AcaciaFund portal.
"""

import pandas as pd
from datetime import datetime, timezone
from transforms.api import transform, Output


@transform(
    test_source=Output("source_dataset")
)
def create_test_data(test_source):
    """
    Creates comprehensive test dataset for AcaciaFund portal.
    Includes: articles, sources, tags, pillars, quality metrics.
    
    This is the first transform in the pipeline - it creates the source dataset
    that all other transforms depend on.
    """
    df = pd.DataFrame({
        "source_id": [f"article_{i:04d}" for i in range(1, 101)],
        "title": [f"Article Title {i}" for i in range(1, 101)],
        "description": [f"Description for article {i}" for i in range(1, 101)],
        "url": [f"https://acaciafund.org/article/{i}" for i in range(1, 101)],
        "source_api": ["arxiv" if i % 5 == 0 else "pubmed" if i % 5 == 1 else "curated"
                       for i in range(1, 101)],
        "domain": ["acaciafund.org"] * 100,
        "tags": [[f"tag_{j}" for j in range(1, (i % 5) + 2)] for i in range(1, 101)],
        "pillar": ["AML" if i % 3 == 0 else "Markets" if i % 3 == 1 else "Data Engineering"
                   for i in range(1, 101)],
        "credibility_score": [round(0.5 + (i % 5) * 0.1, 2) for i in range(1, 101)],
        "technical_accuracy_score": [round(0.6 + (i % 4) * 0.05, 2) for i in range(1, 101)],
        "practical_value_score": [round(0.55 + (i % 6) * 0.05, 2) for i in range(1, 101)],
        "freshness_score": [round(0.7 + (i % 3) * 0.1, 2) for i in range(1, 101)],
        "trend_relevance_score": [round(0.65 + (i % 7) * 0.05, 2) for i in range(1, 101)],
        "educational_quality_score": [round(0.6 + (i % 5) * 0.08, 2) for i in range(1, 101)],
        "trend_strength": [round(80 + (i % 20), 1) for i in range(1, 101)],
        "adoption_level": ["emerging" if i % 3 == 0 else "experimental" if i % 3 == 1 else "mainstream"
                   for i in range(1, 101)],
        "impact_level": ["high" if i % 2 == 0 else "medium" for i in range(1, 101)],
        "inferred_at": [f"2026-06-{15 + (i % 10):02d}T12:00:00+00:00" for i in range(1, 101)],
        "last_updated": ["2026-06-15T12:00:00+00:00"] * 100,
        "is_active": [True if i % 10 != 0 else False for i in range(1, 101)],
        "is_published": [True] * 100,
    })
    
    test_source.write_dataframe(df)
>>>>>>> 6c012ad183030347832ed7189320d8d5eea33762
