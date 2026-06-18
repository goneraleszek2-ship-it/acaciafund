import polars as pl
from transforms.api import transform, Output, LightweightOutput

@transform.using(acacia_portal_clean_data=Output("/TierPalan-95733d/Acacia/acaciafund-pipeline/acacia_portal_clean_data"))
def compute(acacia_portal_clean_data: LightweightOutput) -> None:
    df = pl.DataFrame({"phrase": ["Hello", "World"]})
    acacia_portal_clean_data.write_table(df)
