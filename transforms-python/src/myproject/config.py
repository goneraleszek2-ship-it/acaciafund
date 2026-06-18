"""
AcaciaFund Pipeline Configuration
Centralized configuration for all transforms.
"""

# Dataset Paths - Use relative paths within the project
class DatasetPaths:
    """Centralized dataset path definitions"""
    
    # Input datasets
    SOURCE_DATASET = "SOURCE_DATASET_PATH"
    
    # Output datasets (relative paths within project)
    CLEANED_DATA = "acacia_portal_clean_data"
    QUALITY_SCORES = "quality_scores"
    TREND_ANALYSIS = "trend_analysis"
    ONTOLOGY_CONCEPTS = "ontology_concepts"
    ONTOLOGY_RELATIONSHIPS = "ontology_relationships"
    PROCESSED_DATA = "processed_data"
    CONTENT_CLUSTERS = "content_clusters"
    LEARNING_PATHS = "learning_paths"
    SOURCE_VERIFICATION = "source_verification"
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
