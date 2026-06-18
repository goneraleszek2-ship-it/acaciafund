from transforms.api import Input, Output, transform


@transform(
    input_dataset=Input("/TierPalan-95733d/Acacia/SOURCE_DATASET_PATH"),
    acacia_portal_clean_data=Output(
        "/TierPalan-95733d/Acacia/acacia_portal_clean_data"
    ),
)
def acacia_portal_clean_data(input_dataset, acacia_portal_clean_data):
    """Clean and standardize AcaciaFund portal data"""
    df = input_dataset.polars(lazy=True)
    acacia_portal_clean_data.write_table(df)
