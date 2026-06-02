import pandas as pd
from etl.gems.logger import log

COLS_DROP = [
    "Analysis Method Code",
    "Value Flags",
    "Integrated Value",
    "Remark",
    "License Information",
]

def pre_process_gems_params(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=[c for c in COLS_DROP if c in df.columns])
    df = df.copy()

    fecha_str = df["Sample Date"].astype(str) + " " + df["Sample Time"].astype(str)
    df["fecha_inicio"] = pd.to_datetime(fecha_str, errors="coerce")

    mask = df["fecha_inicio"].isna()
    df.loc[mask, "fecha_inicio"] = pd.to_datetime(df.loc[mask, "Sample Date"], errors="coerce")

    df["fecha_fin"] = df["fecha_inicio"] + pd.Timedelta(days=1)
    df["granularidad"] = "DIA"
    df["value_cat"] = None

    df = df.rename(columns={
        "Parameter Code": "code",
        "Value": "value",
        "Unit": "unit",
        "Data Quality": "data_quality",
        "Depth": "depth",
    })

    df["code"] = df["code"].astype(str).str.strip()
    # Esto es un detalle y por lo que investigamos solo ocurre con pH.
    # pH no tiene dimensionalidad, el dataset oringal lo deja con un string : '---'
    # para que esto sea mas explicito y no lo confundamos con algun error o nulo
    # lo cambiamos a: dimensionless
    df["unit"] = df["unit"].astype(str).str.strip().replace("---", "dimensionless")
    df["data_quality"] = df["data_quality"].astype(str).str.strip()
    df["value"] = pd.to_numeric(df["value"], errors="coerce").astype("float32")
    df["depth"] = pd.to_numeric(df["depth"], errors="coerce").astype("float32")

    df = df.drop(columns=["Sample Date", "Sample Time"])
    n_before = len(df)
    df = df.dropna(subset=["code", "fecha_inicio", "value"])
    log.info(f"pre-process gems_params: {n_before} entrada → {len(df)} salida (nulos_descartados={n_before - len(df)})")

    return df
