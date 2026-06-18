from transforms.api import transform, Input, Output

@transform(
    input_dataset=Input("SOURCE_DATASET_PATH"),
    acacia_portal_clean_data=Output("acacia_portal_clean_data")
)
def compute(input_dataset, acacia_portal_clean_data):
    """
    Clean and standardize AcaciaFund portal data.
    This transform simply copies the input to the output.
    Add your cleaning logic here if needed.
    """
    df = input_dataset.polars(lazy=True)
    acacia_portal_clean_data.write_table(df)
