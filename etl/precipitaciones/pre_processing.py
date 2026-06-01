import pandas as pd


def pre_process(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["fecha_inicio"] = df["fecha"] + pd.Timedelta(hours=9)
    df["fecha_fin"] = df["fecha"] + pd.Timedelta(days=1, hours=8, minutes=59, seconds=59)
    df = df.drop(columns=["fecha"])
    df["granularidad"] = "DIA"
    df = df.dropna(subset=["temperaturaMaxima", "temperaturaMinima", "pluviometro"])
    return df
