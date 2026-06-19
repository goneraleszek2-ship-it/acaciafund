"""
AcaciaFund Pipeline Configuration
Registers all transforms and datasets with proper dependencies.
"""

from transforms.api import Pipelin"""""""""
AcaciaFund Pipeline Configuration
Registers all transforms and datasets automatically.
"""

from transforms.api import Pipeline
from myproject import datasets

# Define the pipeline entry point cleanly without manual config setters
my_pipeline = Pipeline()
my_pipeline.discover_transforms(datasets)
"""