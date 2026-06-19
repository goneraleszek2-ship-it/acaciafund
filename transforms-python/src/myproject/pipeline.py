from transforms.api import Pipeline
from myproject import datasets

# Auto-discover all transforms in the datasets module
my_pipeline = Pipeline()
my_pipeline.discover_transforms(datasets)
