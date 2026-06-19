"""
AcaciaFund Pipeline Configuration
Registers all transforms and datasets with proper dependencies.
"""

from transforms.api import Pipeline

from myproject import datasets
from myproject.config import DatasetPaths, PipelineConfig


my_pipeline = Pipeline()

my_pipeline.discover_transforms(datasets)

my_pipeline.set_config("version", PipelineConfig.VERSION)
