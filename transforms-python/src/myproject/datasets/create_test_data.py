"""
AcaciaFund Test Data Source
Generates realistic test data for the AcaciaFund portal.
"""

import polars as pl
from transforms.api import transform, Output


@transform(
    test_source=Output("SOURCE_DATASET_PATH")
)
def create_test_data(test_source):
    """
    Creates comprehensive test dataset for AcaciaFund portal.
    Includes: articles, sources, tags, pillars, quality metrics.
    
    This is the first transform in the pipeline - it creates the source dataset
    that all other transforms depend on.
    """
    df = pl.DataFrame({
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
        "educational_quality_score": [round(0.6 + (i % 5) * 0.08, 2) for i in r