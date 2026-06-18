"""
AcaciaFund Pipeline Configuration
Centralized configuration for all transforms.
"""

# Dataset Paths
class DatasetPaths:
    """Centralized dataset path definitions"""
    
    # Input datasets
    SOURCE_DATASET = "/TierPalan-95733d/Acacia/SOURCE_DATASET_PATH"
    
    # Output datasets (pipeline)
    CLEANED_DATA = "/TierPalan-95733d/Acacia/acaciafund-pipeline/acacia_portal_clean_data"
    QUALITY_SCORES = "/TierPalan-95733d/Acacia/acaciafund-pipeline/quality_scores"
    TREND_ANALYSIS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/trend_analysis"
    ONTOLOGY_CONCEPTS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/ontology_concepts"
    ONTOLOGY_RELATIONSHIPS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/ontology_relationships"
    PROCESSED_DATA = "/TierPalan-95733d/Acacia/acaciafund-pipeline/processed_data"
    CONTENT_CLUSTERS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/content_clusters"
    LEARNING_PATHS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/learning_paths"
    SOURCE_VERIFICATION = "/TierPalan-95733d/Acacia/acaciafund-pipeline/source_verification"
    SOURCE_SYNTHESIS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/source_synthesis"
    EXPORT_QUALITY_METRICS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/export_quality_metrics"
    EXPORT_TECHNOLOGY_RADAR = "/TierPalan-95733d/Acacia/acaciafund-pipeline/export_technology_radar"
    EXPORT_SOURCE_SYNTHESIS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/export_source_synthesis"
    INCREMENTAL_UPDATES = "/TierPalan-95733d/Acacia/acaciafund-pipeline/incremental_fund_updates"
    CLEANING_QUALITY_METRICS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/cleaning_quality_metrics"
    DATA_QUALITY_REPORT = "/TierPalan-95733d/Acacia/acaciafund-pipeline/data_quality_report"
    DATA_QUALITY_ALERTS = "/TierPalan-95733d/Acacia/acaciafund-pipeline/data_quality_alerts"
    PIPELINE_HEALTH = "/TierPalan-95733d/Acacia/acaciafund-pipeline/pipeline_health"
    TRANSFORM_HEALTH = "/TierPalan-95733d/Acacia/acaciafund-pipeline/transform_health"


# Data Quality Thresholds
class QualityThresholds:
    """Data quality thresholds for alerts and filtering"""
    
    MIN_CREDIBILITY_SCORE = 0.5
    MIN_OVERALL_QUALITY_SCORE = 0.6
    MIN_TREND_STRENGTH = 50
    MAX_NULL_PERCENTAGE = 10.0
    MAX_DUPLICATE_PERCENTAGE = 5.0


# Pipeline Configuration
class PipelineConfig:
    """Pipeline-wide configuration"""
    
    VERSION = "2.0.0"
    DEFAULT_OUTPUT_VERSION = "v2.0"
    DEFAULT_TIMESTAMP = "ingestion_timestamp"
    
    # Batch settings
    BATCH_SIZE = 10000
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_TO_FILE = True
    LOG_FILE_PATH = "/var/log/acaciafund/pipeline.log"
