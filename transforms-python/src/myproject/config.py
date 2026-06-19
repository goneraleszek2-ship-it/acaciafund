"""
AcaciaFund Pipeline Configuration
Centralized configuration for all transforms.
"""


class DatasetPaths:
    SOURCE_DATASET = "source_dataset"
    CLEANED_DATA = "acacia_portal_clean_data"
    CLEANED_DATA_ENHANCED = "acacia_portal_clean_data_enhanced"
    QUALITY_SCORES = "quality_scores"
    SOURCE_VERIFICATION = "source_verification"
    SOURCE_METADATA = "source_metadata"
    TREND_ANALYSIS = "trend_analysis"
    TECHNOLOGY_RADAR = "technology_radar"
    ONTOLOGY_CONCEPTS = "ontology_concepts"
    ONTOLOGY_RELATIONSHIPS = "ontology_relationships"
    PROCESSED_DATA = "processed_data"
    CONTENT_CLUSTERS = "content_clusters"
    LEARNING_PATHS = "learning_paths"
    SOURCE_SYNTHESIS = "source_synthesis"
    EXPORT_QUALITY_METRICS = "export_quality_metrics"
    EXPORT_TECHNOLOGY_RADAR = "export_technology_radar"
    EXPORT_SOURCE_SYNTHESIS = "export_source_synthesis"
    INCREMENTAL_UPDATES = "incremental_fund_updates"
    CLEANING_QUALITY_METRICS = "cleaning_quality_metrics"
    DATA_QUALITY_REPORT = "data_quality_report"
    DATA_QUALITY_ALERTS = "data_quality_alerts"
    PIPELINE_HEALTH = "pipeline_health"
    TRANSFORM_HEALTH = "transform_health"
    FUND_ANALYTICS = "fund_analytics"


class QualityThresholds:
    MIN_CREDIBILITY_SCORE = 0.5
    MIN_OVERALL_QUALITY_SCORE = 0.6
    MIN_TREND_STRENGTH = 50
    MAX_NULL_PERCENTAGE = 10.0
    MAX_DUPLICATE_PERCENTAGE = 5.0


class PipelineConfig:
    VERSION = "3.0.0"
