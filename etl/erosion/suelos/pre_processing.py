import geopandas as pd

def pre_process(df: pd.GeoDataFrame) -> pd.GeoDataFrame:
    df_nona = df.dropna(subset=["Factor_K"])
    return df_nona