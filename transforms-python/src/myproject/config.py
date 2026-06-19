"""
AcaciaFund Pipeline Configuration
Centralized configuration for all transforms.
"""

_PREFIX = "/TierPalan-95733d/Acacia/acaciafund-pipeline"


class DatasetPaths:
    SOURCE_DATASET = f"{_PREFIX}/source_dataset"
    CLEANED_DATA = f"{_PREFIX}/acacia_portal_clean_data"
    CLEANED_DATA_ENHANCED = f"{_PREFIX}/acacia_portal_clean_data_enhanced"
    QUALITY_SCORES = f"{_PREFIX}/quality_scores"
    SOURCE_VERIFICATION = f"{_PREFIX}/source_verification"
    SOURCE_METADATA = f"{_PREFIX}/source_metadata"
    TREND_ANALYSIS = f"{_PREFIX}/trend_analysis"
    TECHNOLOGY_RADAR = f"{_PREFIX}/technology_radar"
    ONTOLOGY_CONCEPTS = f"{_PREFIX}/ontology_concepts"
    ONTOLOGY_RELATIONSHIPS = f"{_PREFIX}/ontology_relationships"
    PROCESSED_DATA = f"{_PREFIX}/processed_data"
    CONTENT_CLUSTERS = f"{_PREFIX}/content_clusters"
    LEARNING_PATHS = f"{_PREFIX}/learning_paths"
    SOURCE_SYNTHESIS = f"{_PREFIX}/source_synthesis"
    EXPORT_QUALITY_METRICS = f"{_PREFIX}/export_quality_metrics"
    EXPORT_TECHNOLOGY_RADAR = f"{_PREFIX}/export_technology_radar"
    EXPORT_SOURCE_SYNTHESIS = f"{_PREFIX}/export_source_synthesis"
    INCREMENTAL_UPDATES = f"{_PREFIX}/incremental_fund_updates"
    CLEANING_QUALITY_METRICS = f"{_PREFIX}/cleaning_quality_metrics"
    DATA_QUALITY_REPORT = f"{_PREFIX}/data_quality_report"
    DATA_QUALITY_ALERTS = f"{_PREFIX}/data_quality_alerts"
    PIPELINE_HEALTH = f"{_PREFIX}/pipeline_health"
    TRANSFORM_HEALTH = f"{_PREFIX}/transform_health"
    FUND_ANALYTICS = f"{_PREFIX}/fund_analytics"


class QualityThresholds:
    MIN_CREDIBILITY_SCORE = 0.5
    MIN_OVERALL_QUALITY_SCORE = 0.6
    MIN_TREND_STRENGTH = 50
    MAX_NULL_PERCENTAGE = 10.0
    MAX_DUPLICATE_PERCENTAGE = 5.0


class PipelineConfig:
    VERSION = "4.0.0"
