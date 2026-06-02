import pandas as pd
from etl.inumet.logger import log

def pre_process_precipitacion(df: pd.DataFrame) -> pd.DataFrame:
    n_orig = len(df)
    df = df.dropna(subset=["fecha", "estacion_id", "precip_horario"])
    df = df.copy()

    df["estacion_id"] = df["estacion_id"].astype(str).str.strip()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["precip_horario"] = pd.to_numeric(df["precip_horario"], errors="coerce")

    df = df.dropna(subset=["fecha", "estacion_id", "precip_horario"])
    log.info(f"pre-process precipitacion: {n_orig} entrada → {len(df)} salida (descartados={n_orig - len(df)})")
    return df

def pre_process_humedad_relativa(df: pd.DataFrame) -> pd.DataFrame:
    n_orig = len(df)
    df = df.dropna(subset=["fecha", "estacion_id", "hum_relativa"])
    df = df.copy()

    df["estacion_id"] = df["estacion_id"].astype(str).str.strip()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["hum_relativa"] = pd.to_numeric(df["hum_relativa"], errors="coerce")

    df = df.dropna(subset=["fecha", "estacion_id", "hum_relativa"])
    log.info(f"pre-process humedad_relativa: {n_orig} entrada → {len(df)} salida (descartados={n_orig - len(df)})")
    return df