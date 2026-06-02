import geopandas as pd
from etl.erosion.suelos.logger import log

def pre_process(df: pd.GeoDataFrame) -> pd.GeoDataFrame:
    n_orig = len(df)
    df_nona = df.dropna(subset=["Factor_K"])
    dropped = n_orig - len(df_nona)
    log.info(f"pre-process: {n_orig} entrada → {len(df_nona)} salida (Factor_K_nulo={dropped})")
    return df_nona