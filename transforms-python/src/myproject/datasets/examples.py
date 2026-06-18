# # import polars as pl
# from transforms.api import Input, Output, transform, LightweightInput, LightweightOutput
# 
# 
# @transform.using(
#     output_dataset=Output("/TierPalan-96733d/Acacia/TARGET_DATASET_PATH"),
#     input_dataset=Input("/TierPalan-96733d/Acacia/SOURCE_DATASET_PATH"),
# )
# def compute(input_dataset: LightweightInput, output_dataset: LightweightOutput) -> None:
#     output_dataset.write_table(input_dataset.polars(lazy=True))
# 