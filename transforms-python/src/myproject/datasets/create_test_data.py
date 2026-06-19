"""
AcaciaFund Test Data Source
Generates realistic test data for the AcaciaFund portal.
"""
import pandas as pd
from transforms.api import transform, Output, TransformOutput

@transform(
    # FIX: Prepended a leading '/' to make this a valid absolute path for Shrinkwrap
    test_source=Output("/Acacia/acaciafund-pipeline/mock_source_data")
)
def create_test_data(test_source: TransformOutput) -> None:                  
    df = pd.DataFrame({
        "source_id": [f"article_{i:04d}" for i in range(1, 101)],
        "title": [f"Article Title {i}" for i in range(1, 101)],
        "description": [f"Description for article {i}" for i in range(1, 101)],
        "url": [f"https://acaciafund.org/{i}" for i in range(1, 101)],
        "source_api": ["arxiv" if i % 5 == 0 else "pubmed" for i in range(1, 101)],
        "domain": ["acaciafund.org"] * 100,
        "tags": [",".join([f"tag_{j}" for j in range(1, (i % 5) + 2)]) for i in range(1, 101)],
        "pillar": ["AML" if i % 3 == 0 else "Markets" if i % 3 == 1 else "Tech" for i in range(1, 101)],
        "credibility_score": [round(0.5 + (i % 5) * 0.1, 2) for i in range(1, 101)],
        "technical_accuracy_score": [round(0.6 + (i % 4) * 0.1, 2) for i in range(1, 101)],
        "practical_value_score": [round(0.55 + (i % 6) * 0.08, 2) for i in range(1, 101)],
        "freshness_score": [round(0.7 + (i % 3) * 0.1, 2) for i in range(1, 101)],
        "trend_relevance_score": [round(0.65 + (i % 7) * 0.05, 2) for i in range(1, 101)],
        "educational_quality_score": [round(0.6 + (i % 5) * 0.09, 2) for i in range(1, 101)],
        "trend_strength": [round(80 + (i % 20), 1) for i in range(1, 101)],
        "adoption_level": ["emerging" if i % 3 == 0 else "growing" if i % 3 == 1 else "mature" for i in range(1, 101)],
        "impact_level": ["high" if i % 2 == 0 else "medium" for i in range(1, 101)],
        "inferred_at": [f"2026-06-{15 + (i % 10):02d}T12:00:00+00:00" for i in range(1, 101)],
        "last_updated": ["2026-06-15T12:00:00+00:00"] * 100,
        "is_active": [i % 10 != 0 for i in range(1, 101)],
        "is_published": [True] * 100,
    })
    
    # Run the quality mapping calculation
    df["composite_quality_score"] = (
        (df["credibility_score"] * 0.4) + 
        (df["technical_accuracy_score"] * 0.4) + 
        (df["practical_value_score"] * 0.2)
    ).round(2)
    
    test_source.write_pandas(df)
