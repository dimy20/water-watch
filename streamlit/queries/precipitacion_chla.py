import pandas as pd

# Espaciado de la grilla PAD ~0.3333° (~37km). Estaciones a más de esta
# distancia del punto de grilla más cercano se consideran sin cobertura PAD.
PAD_MAX_DISTANCIA_M = 40_000

ESTACIONES_RECOMENDADAS = [
    "URY00076",
    "URY00031",
    "URY00046",
    "URY00045",
    "URY00047",
    "URY00035",
    "URY00135",
    "URY00134",
    "URY00130",
    "URY00129",
]


def _periodo_naive(serie: pd.Series) -> pd.Series:
    serie = pd.to_datetime(serie)
    if serie.dt.tz is not None:
        serie = serie.dt.tz_convert(None)
    return serie


def get_estaciones_con_chla(pg_conn, mongo_db) -> pd.DataFrame:
    cur = pg_conn.cursor()
    cur.execute("SELECT DISTINCT location_id FROM gemsparams WHERE code = 'Chl-a'")
    location_ids = [row[0] for row in cur.fetchall()]

    if not location_ids:
        return pd.DataFrame(columns=["location_id", "nombre"])

    docs = mongo_db["estaciones"].find({"_id": {"$in": location_ids}}, {"_id": 1, "nombre": 1})
    nombres = {d["_id"]: d["nombre"] for d in docs}

    df = pd.DataFrame({"location_id": location_ids})
    df["nombre"] = df["location_id"].map(nombres)
    df = df.dropna(subset=["nombre"])

    df = df[df["nombre"].isin(ESTACIONES_RECOMENDADAS)]

    df = df[df["location_id"].apply(
        lambda lid: get_punto_grilla_cercano(mongo_db, lid, PAD_MAX_DISTANCIA_M) is not None
    )]
    return df.reset_index(drop=True)


def get_punto_grilla_cercano(mongo_db, location_id, max_distance_m=None):
    estacion = mongo_db["estaciones"].find_one({"_id": location_id}, {"location": 1})
    if not estacion:
        return None

    near = {"$geometry": estacion["location"]}
    if max_distance_m is not None:
        near["$maxDistance"] = max_distance_m

    punto = mongo_db["puntos_grilla"].find_one(
        {"location": {"$nearSphere": near}},
        {"_id": 1},
    )
    return punto["_id"] if punto else None


def get_pad_mensual(pg_conn, punto_id, anio_inicio, anio_fin) -> pd.DataFrame:
    sql = """
        SELECT DATE_TRUNC('month', fecha_inicio) AS periodo, AVG(value) AS pad
        FROM puntomedicion
        WHERE punto_id = %s
          AND type = 'PAD'
          AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY periodo
        ORDER BY periodo
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (punto_id, anio_inicio, anio_fin))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["periodo", "pad"])
    df["periodo"] = _periodo_naive(df["periodo"])
    df["pad"] = df["pad"].astype(float)
    return df


def get_chla_mensual(pg_conn, location_id, anio_inicio, anio_fin) -> pd.DataFrame:
    sql = """
        SELECT DATE_TRUNC('month', fecha_inicio) AS periodo, AVG(value) AS chla
        FROM gemsparams
        WHERE code = 'Chl-a'
          AND location_id = %s
          AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY periodo
        ORDER BY periodo
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (location_id, anio_inicio, anio_fin))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["periodo", "chla"])
    df["periodo"] = _periodo_naive(df["periodo"])
    df["chla"] = df["chla"].astype(float)
    return df


def _reindex_mensual(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    rango = pd.date_range(df["periodo"].min(), df["periodo"].max(), freq="MS")
    return (
        df.set_index("periodo")
        .reindex(rango)
        .rename_axis("periodo")
        .reset_index()
    )


def combinar_precip_chla(df_pad: pd.DataFrame, df_chla: pd.DataFrame, lag_meses: int = 1) -> pd.DataFrame:
    df_pad = df_pad.copy()
    df_pad["periodo_lag"] = df_pad["periodo"] + pd.DateOffset(months=lag_meses)

    merged = df_chla.merge(
        df_pad[["periodo_lag", "pad"]],
        left_on="periodo",
        right_on="periodo_lag",
        how="outer",
    )
    merged["periodo"] = merged["periodo"].fillna(merged["periodo_lag"])
    merged = merged.drop(columns=["periodo_lag"]).sort_values("periodo").reset_index(drop=True)
    return _reindex_mensual(merged[["periodo", "pad", "chla"]])


def get_precipitacion_vs_chla(pg_conn, mongo_db, location_id, anio_inicio, anio_fin, lag_meses: int = 1) -> pd.DataFrame:
    df_chla = get_chla_mensual(pg_conn, location_id, anio_inicio, anio_fin)

    punto_id = get_punto_grilla_cercano(mongo_db, location_id, PAD_MAX_DISTANCIA_M)
    if punto_id is None:
        df_chla["pad"] = pd.NA
        return _reindex_mensual(df_chla[["periodo", "pad", "chla"]])

    df_pad = get_pad_mensual(pg_conn, punto_id, anio_inicio, anio_fin)
    return combinar_precip_chla(df_pad, df_chla, lag_meses)
