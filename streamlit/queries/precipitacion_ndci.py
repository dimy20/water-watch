import pandas as pd
from shapely.geometry import shape, mapping

# Espaciado de la grilla PAD ~0.3333° (~37km). Puntos a más de esta
# distancia del punto de grilla más cercano se consideran sin cobertura PAD.
PAD_MAX_DISTANCIA_M = 40_000


def _periodo_naive(serie: pd.Series) -> pd.Series:
    serie = pd.to_datetime(serie)
    if serie.dt.tz is not None:
        serie = serie.dt.tz_convert(None)
    return serie


def get_locations_con_ndci(pg_conn, mongo_db) -> pd.DataFrame:
    cur = pg_conn.cursor()
    cur.execute("SELECT DISTINCT location_id FROM sentinel_params WHERE code = 'NDCI'")
    location_ids = [row[0] for row in cur.fetchall()]

    if not location_ids:
        return pd.DataFrame(columns=["location_id", "nombre", "lat", "lon"])

    docs = mongo_db["sentinel_locations"].find(
        {"_id": {"$in": location_ids}}, {"_id": 1, "nombre": 1, "geometry": 1}
    )
    info = {}
    for d in docs:
        centroide = shape(d["geometry"]).centroid
        info[d["_id"]] = {"nombre": d["nombre"], "lat": centroide.y, "lon": centroide.x}

    df = pd.DataFrame({"location_id": location_ids})
    df["nombre"] = df["location_id"].map(lambda lid: info.get(lid, {}).get("nombre"))
    df["lat"] = df["location_id"].map(lambda lid: info.get(lid, {}).get("lat"))
    df["lon"] = df["location_id"].map(lambda lid: info.get(lid, {}).get("lon"))
    df = df.dropna(subset=["nombre"])

    df = df[df["location_id"].apply(
        lambda lid: get_punto_grilla_cercano_sentinel(mongo_db, lid, PAD_MAX_DISTANCIA_M) is not None
    )]
    return df.reset_index(drop=True)


def get_punto_grilla_cercano_sentinel(mongo_db, location_id, max_distance_m=None):
    location = mongo_db["sentinel_locations"].find_one({"_id": location_id}, {"geometry": 1})
    if not location:
        return None

    centroide = shape(location["geometry"]).centroid

    near = {"$geometry": mapping(centroide)}
    if max_distance_m is not None:
        near["$maxDistance"] = max_distance_m

    punto = mongo_db["puntos_grilla"].find_one(
        {"location": {"$nearSphere": near}},
        {"_id": 1},
    )
    return punto["_id"] if punto else None


def get_punto_grilla_coords(mongo_db, punto_id):
    punto = mongo_db["puntos_grilla"].find_one({"_id": punto_id}, {"location": 1})
    if not punto:
        return None

    lon, lat = punto["location"]["coordinates"]
    return lat, lon


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


def get_ndci_mensual(pg_conn, location_id, anio_inicio, anio_fin) -> pd.DataFrame:
    sql = """
        SELECT DATE_TRUNC('month', fecha_inicio) AS periodo, AVG(value) AS ndci
        FROM sentinel_params
        WHERE code = 'NDCI'
          AND location_id = %s
          AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY periodo
        ORDER BY periodo
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (location_id, anio_inicio, anio_fin))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["periodo", "ndci"])
    df["periodo"] = _periodo_naive(df["periodo"])
    df["ndci"] = df["ndci"].astype(float)
    return df


def _nombres_sentinel_locations(mongo_db, location_ids) -> dict:
    docs = mongo_db["sentinel_locations"].find(
        {"_id": {"$in": list(location_ids)}},
        {"_id": 1, "nombre": 1},
    )
    return {doc["_id"]: doc["nombre"] for doc in docs}


def get_ndci_resumen_cuerpos_agua(pg_conn, mongo_db, anio_inicio, anio_fin) -> pd.DataFrame:
    sql = """
        SELECT location_id,
               COUNT(*) AS observaciones,
               MIN(fecha_inicio) AS fecha_min,
               MAX(fecha_inicio) AS fecha_max,
               AVG(value) AS ndci_promedio,
               MIN(value) AS ndci_min,
               MAX(value) AS ndci_max,
               STDDEV_SAMP(value) AS ndci_desvio
        FROM sentinel_params
        WHERE code = 'NDCI'
          AND fecha_inicio >= make_date(%s, 1, 1)
          AND fecha_inicio < make_date(%s + 1, 1, 1)
        GROUP BY location_id
        ORDER BY ndci_promedio DESC
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (anio_inicio, anio_fin))
    rows = cur.fetchall()
    columns = [
        "location_id",
        "observaciones",
        "fecha_min",
        "fecha_max",
        "ndci_promedio",
        "ndci_min",
        "ndci_max",
        "ndci_desvio",
    ]
    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        return pd.DataFrame(columns=["nombre", *columns[1:]])

    nombres = _nombres_sentinel_locations(mongo_db, df["location_id"].tolist())
    df["nombre"] = df["location_id"].map(nombres)
    df = df.dropna(subset=["nombre"])

    for col in ["ndci_promedio", "ndci_min", "ndci_max", "ndci_desvio"]:
        df[col] = df[col].astype(float)

    return df[
        [
            "nombre",
            "observaciones",
            "fecha_min",
            "fecha_max",
            "ndci_promedio",
            "ndci_min",
            "ndci_max",
            "ndci_desvio",
        ]
    ].reset_index(drop=True)


def get_ndci_mensual_cuerpos_agua(pg_conn, mongo_db, anio_inicio, anio_fin) -> pd.DataFrame:
    sql = """
        SELECT location_id,
               DATE_TRUNC('month', fecha_inicio)::date AS mes,
               COUNT(*) AS observaciones,
               AVG(value) AS ndci_promedio
        FROM sentinel_params
        WHERE code = 'NDCI'
          AND fecha_inicio >= make_date(%s, 1, 1)
          AND fecha_inicio < make_date(%s + 1, 1, 1)
        GROUP BY location_id, mes
        ORDER BY location_id, mes
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (anio_inicio, anio_fin))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["location_id", "mes", "observaciones", "ndci_promedio"])
    if df.empty:
        return pd.DataFrame(columns=["nombre", "mes", "observaciones", "ndci_promedio"])

    nombres = _nombres_sentinel_locations(mongo_db, df["location_id"].tolist())
    df["nombre"] = df["location_id"].map(nombres)
    df = df.dropna(subset=["nombre"])
    df["mes"] = pd.to_datetime(df["mes"])
    df["ndci_promedio"] = df["ndci_promedio"].astype(float)
    return df[["nombre", "mes", "observaciones", "ndci_promedio"]].reset_index(drop=True)


def get_ndci_observaciones_cuerpos_agua(pg_conn, mongo_db, anio_inicio, anio_fin) -> pd.DataFrame:
    sql = """
        SELECT location_id,
               fecha_inicio,
               value AS ndci
        FROM sentinel_params
        WHERE code = 'NDCI'
          AND fecha_inicio >= make_date(%s, 1, 1)
          AND fecha_inicio < make_date(%s + 1, 1, 1)
        ORDER BY location_id, fecha_inicio
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (anio_inicio, anio_fin))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["location_id", "fecha_inicio", "ndci"])
    if df.empty:
        return pd.DataFrame(columns=["nombre", "fecha_inicio", "ndci"])

    nombres = _nombres_sentinel_locations(mongo_db, df["location_id"].tolist())
    df["nombre"] = df["location_id"].map(nombres)
    df = df.dropna(subset=["nombre"])
    df["ndci"] = df["ndci"].astype(float)
    return df[["nombre", "fecha_inicio", "ndci"]].reset_index(drop=True)


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


def combinar_precip_ndci(df_pad: pd.DataFrame, df_ndci: pd.DataFrame, lag_meses: int = 1) -> pd.DataFrame:
    df_pad = df_pad.copy()
    df_pad["periodo_lag"] = df_pad["periodo"] + pd.DateOffset(months=lag_meses)

    merged = df_ndci.merge(
        df_pad[["periodo", "periodo_lag", "pad"]].rename(columns={"periodo": "pad_periodo"}),
        left_on="periodo",
        right_on="periodo_lag",
        how="outer",
    )
    merged["periodo"] = merged["periodo"].fillna(merged["periodo_lag"])
    merged = merged.drop(columns=["periodo_lag"]).sort_values("periodo").reset_index(drop=True)
    return _reindex_mensual(merged[["periodo", "pad", "pad_periodo", "ndci"]])


def get_precipitacion_vs_ndci(pg_conn, mongo_db, location_id, anio_inicio, anio_fin, lag_meses: int = 1) -> pd.DataFrame:
    df_ndci = get_ndci_mensual(pg_conn, location_id, anio_inicio, anio_fin)

    punto_id = get_punto_grilla_cercano_sentinel(mongo_db, location_id, PAD_MAX_DISTANCIA_M)
    if punto_id is None:
        df_ndci["pad"] = pd.NA
        df_ndci["pad_periodo"] = pd.NaT
        return _reindex_mensual(df_ndci[["periodo", "pad", "pad_periodo", "ndci"]])

    df_pad = get_pad_mensual(pg_conn, punto_id, anio_inicio, anio_fin)
    return combinar_precip_ndci(df_pad, df_ndci, lag_meses)


def get_correlacion_por_lag(pg_conn, mongo_db, location_id, anio_inicio, anio_fin, lag_max: int = 6) -> pd.DataFrame:
    df_ndci = get_ndci_mensual(pg_conn, location_id, anio_inicio, anio_fin)

    punto_id = get_punto_grilla_cercano_sentinel(mongo_db, location_id, PAD_MAX_DISTANCIA_M)
    if punto_id is None:
        return pd.DataFrame(columns=["lag", "correlacion", "n"])

    df_pad = get_pad_mensual(pg_conn, punto_id, anio_inicio, anio_fin)

    result = []
    for lag in range(lag_max + 1):
        combinado = combinar_precip_ndci(df_pad, df_ndci, lag)
        validos = combinado.dropna(subset=["pad", "ndci"])
        n = len(validos)
        correlacion = validos["pad"].corr(validos["ndci"]) if n >= 3 else float("nan")
        result.append({"lag": lag, "correlacion": correlacion, "n": n})

    return pd.DataFrame(result)
