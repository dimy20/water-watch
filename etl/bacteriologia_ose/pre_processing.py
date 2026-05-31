import unicodedata
import pandas as pd

TRIMESTRE_INICIO = {1: "01-01", 2: "04-01", 3: "07-01", 4: "10-01"}
TRIMESTRE_FIN    = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}

COLS_DROP = ["area_analisis", "metodo", "laboratorio", "localidad"]

def normalizar_nombre(s: str) -> str:
    s = s.lower().strip()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def pre_process(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=[c for c in COLS_DROP if c in df.columns]).copy()
    df = df[df["valor"] != "<1"]

    num = df["trimestre"].str.extract(r"(\d)").astype(int)[0]
    df["fecha_inicio"] = pd.to_datetime(df["año"].astype(str) + "-" + num.map(TRIMESTRE_INICIO))
    df["fecha_fin"]    = pd.to_datetime(df["año"].astype(str) + "-" + num.map(TRIMESTRE_FIN))

    df = df.rename(columns={"parametro": "code", "valor": "value_cat"})
    df["value"] = None
    df["granularidad"] = "TRIMESTRE"

    df = df.drop(columns=["año", "trimestre"])
    return df
