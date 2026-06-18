from transforms.api import transform, Input, Output

@transform(
    input_dataset=Input("/TierPalan-95733d/Acacia/SOURCE_DATASET_PATH"),
    acacia_portal_clean_data=Output("/TierPalan-95733d/Acacia/acacia_portal_clean_data")
)
def compute(input_dataset, acacia_portal_clean_data):
    df = input_dataset.polars(lazy=True)
    acacia_portal_clean_data.write_table(df)