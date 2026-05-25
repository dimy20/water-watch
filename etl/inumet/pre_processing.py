import pandas as pd

# Pre procesamiento para fuentes de inumet

def pre_process_precipitacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["fecha", "estacion_id", "precip_horario"])
    df = df.copy()

    df["estacion_id"] = df["estacion_id"].astype(str).str.strip()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["precip_horario"] = pd.to_numeric(df["precip_horario"], errors="coerce")

    df = df.dropna(subset=["fecha", "estacion_id", "precip_horario"])
    return df

def pre_process_humedad_relativa(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["fecha", "estacion_id", "hum_relativa"])
    df = df.copy()

    df["estacion_id"] = df["estacion_id"].astype(str).str.strip()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["hum_relativa"] = pd.to_numeric(df["hum_relativa"], errors="coerce")

    df = df.dropna(subset=["fecha", "estacion_id", "hum_relativa"])

    return df