"""
AcaciaFund Pipeline Configuration
Registers all transforms and datasets with proper dependencies.
"""

from transforms.api import Pipeline

from myproject import datasets
from myproject.config import DatasetPaths, QualityThresholds, PipelineConfig


my_pipeline = Pipeline()

# Discover all transforms
my_pipeline.discover_transforms(datasets)

# Configure pipeline settings
my_pipeline.set_config("version", PipelineConfig.VERSION)
my_pipeline.set_config("default_output_version", PipelineConfig.DEFAULT_OUTPUT_VERSION)

# Set up data quality thresholds
my_pipeline.set_config("quality_thresholds", {
    "min_credibility": QualityThresholds.MIN_CREDIBILITY_SCORE,
    "min_overall_quality": QualityThresholds.MIN_OVERALL_QUALITY_SCORE,
    "min_trend_strength": QualityThresholds.MIN_TREND_STRENGTH,
    "max_null_percentage": QualityThresholds.MAX_NULL_PERCENTAGE,
    "max_duplicate_percentage": QualityThresholds.MAX_DUPLICATE_PERCENTAGE,
})

# Set up dataset paths
my_pipeline.set_config("dataset_paths", {
    "source_dataset": DatasetPaths.SOURCE_DATASET,
    "cleaned_data": DatasetPaths.CLEANED_DATA,
    "quality_scores": DatasetPaths.QUALITY_SCORES,
    "trend_analysis": DatasetPaths.TREND_ANALYSIS,
    "ontology_concepts": DatasetPaths.ONTOLOGY_CONCEPTS,
    "processed_data": DatasetPaths.PROCESSED_DATA,
    "content_clusters": DatasetPaths.CONTENT_CLUSTERS,
    "learning_paths": DatasetPaths.LEARNING_PATHS,
    "source_verification": DatasetPaths.SOURCE_VERIFICATION,
    "source_synthesis": DatasetPaths.SOURCE_SYNTHESIS,
    "export_quality_metrics": DatasetPaths.EXPORT_QUALITY_METRICS,
    "export_technology_radar": DatasetPaths.EXPORT_TECHNOLOGY_RADAR,
    "export_source_synthesis": DatasetPaths.EXPORT_SOURCE_SYNTHESIS,
    "incremental_updates": DatasetPaths.INCREMENTAL_UPDATES,
    "cleaning_quality_metrics": DatasetPaths.CLEANING_QUALITY_METRICS,
    "data_quality_report": DatasetPaths.DATA_QUALITY_REPORT,
    "data_quality_alerts": DatasetPaths.DATA_QUALITY_ALERTS,
    "pipeline_health": DatasetPaths.PIPELINE_HEALTH,
    "transform_health": DatasetPaths.TRANSFORM_HEALTH,
})

# Configure transform execution order (implicit via dependencies)
# Transforms will execute in dependency order automatically
my_pipeline.set_config("execution_order", [
    "create_test_data",
    "ingestion",
    "lightweight-transform",  # Clean and standardize
    "enhanced_cleaning",
    "scoring",
    "analysis",
    "ontology",
    "processing",  # Data enrichment
    "source_synthesis",
    "export",  # Static exports
    "fund_analytics",
    "incremental_updates",
    "data_quality",  # Quality checks
    "health_checks",  # Health monitoring
])

print(f"AcaciaFund Pipeline configured successfully (v{PipelineConfig.VERSION})")
print(f"Total transforms registered: {len(my_pipeline.transforms)}")
print(f"Total datasets configured: {len(my_pipeline.datasets)}")
