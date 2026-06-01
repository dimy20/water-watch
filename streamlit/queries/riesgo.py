import pandas as pd

from .grillas import get_hidrico_suelo_por_departamento


def _minmax(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if valid.empty or valid.max() == valid.min():
        return series.where(series.isna(), 0.0)
    mn, mx = valid.min(), valid.max()
    return (series - mn) / (mx - mn)


def _get_contam_ose(pg_conn, mongo_db, anio_inicio, anio_fin) -> pd.DataFrame:
    sql = """
        SELECT departamento_id,
            SUM(CASE WHEN value_cat = 'Presencia' THEN total ELSE 0 END) * 100.0 / SUM(total) AS pct_ose
        FROM (
            SELECT departamento_id, value_cat, COUNT(*) AS total
            FROM oseparam
            WHERE code = 'COLIFORMES TOTALES'
              AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
            GROUP BY departamento_id, value_cat
        ) sub
        GROUP BY departamento_id
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (anio_inicio, anio_fin))
    rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=["nombre", "pct_ose"])
    df = pd.DataFrame(rows, columns=["departamento_id", "pct_ose"])
    uuids = df["departamento_id"].tolist()
    docs = mongo_db["departamentos"].find({"_id": {"$in": uuids}}, {"_id": 1, "nombre": 1})
    nombres = {d["_id"]: d["nombre"] for d in docs}
    df["nombre"] = df["departamento_id"].map(nombres)
    df["pct_ose"] = df["pct_ose"].astype(float)
    return df[["nombre", "pct_ose"]].dropna(subset=["nombre"])


def _get_contam_gems(pg_conn, mongo_db, anio_inicio, anio_fin) -> pd.DataFrame:
    departamentos = list(mongo_db["departamentos"].find({}, {"_id": 1, "nombre": 1, "geometry": 1}))

    location_map = {}
    for depto in departamentos:
        ids = [e["_id"] for e in mongo_db["estaciones"].find(
            {"location": {"$geoWithin": {"$geometry": depto["geometry"]}}},
            {"_id": 1},
        )]
        if ids:
            location_map[depto["nombre"]] = ids

    if not location_map:
        return pd.DataFrame(columns=["nombre", "val_gems"])

    all_ids = [lid for ids in location_map.values() for lid in ids]
    sql = """
        SELECT location_id, AVG(value) AS val_gems
        FROM gemsparams
        WHERE location_id = ANY(%s)
          AND code = 'TOTCOLI'
          AND value IS NOT NULL
          AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY location_id
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (all_ids, anio_inicio, anio_fin))
    station_avg = {row[0]: float(row[1]) for row in cur.fetchall()}

    result = [
        {"nombre": nombre, "val_gems": sum(station_avg[i] for i in ids if i in station_avg) / len([i for i in ids if i in station_avg])}
        for nombre, ids in location_map.items()
        if any(i in station_avg for i in ids)
    ]
    return pd.DataFrame(result) if result else pd.DataFrame(columns=["nombre", "val_gems"])


def _get_precip_por_departamento(pg_conn, mongo_db, anio_inicio, anio_fin) -> pd.DataFrame:
    departamentos = list(mongo_db["departamentos"].find({}, {"_id": 1, "nombre": 1, "geometry": 1}))

    location_map = {}
    for depto in departamentos:
        ids = [e["_id"] for e in mongo_db["estaciones"].find(
            {"location": {"$geoWithin": {"$geometry": depto["geometry"]}}},
            {"_id": 1},
        )]
        if ids:
            location_map[depto["nombre"]] = ids

    if not location_map:
        return pd.DataFrame(columns=["nombre", "val_precip"])

    all_ids = [lid for ids in location_map.values() for lid in ids]
    sql = """
        SELECT location_id, AVG(pluviometro) AS val_precip
        FROM registrotempprec
        WHERE location_id = ANY(%s)
          AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY location_id
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (all_ids, anio_inicio, anio_fin))
    station_avg = {row[0]: float(row[1]) for row in cur.fetchall()}

    result = [
        {"nombre": nombre, "val_precip": sum(station_avg[i] for i in ids if i in station_avg) / len([i for i in ids if i in station_avg])}
        for nombre, ids in location_map.items()
        if any(i in station_avg for i in ids)
    ]
    return pd.DataFrame(result) if result else pd.DataFrame(columns=["nombre", "val_precip"])


def get_riesgo_por_departamento(mongo_db, pg_conn, anio_inicio, anio_fin) -> pd.DataFrame:
    df_ose = _get_contam_ose(pg_conn, mongo_db, anio_inicio, anio_fin)
    df_gems = _get_contam_gems(pg_conn, mongo_db, anio_inicio, anio_fin)
    df_precip = _get_precip_por_departamento(pg_conn, mongo_db, anio_inicio, anio_fin)
    df_ibh = get_hidrico_suelo_por_departamento(mongo_db, pg_conn, "IBH", anio_inicio, anio_fin)
    df_ibh = df_ibh.rename(columns={"valor_medio": "val_suelo"})

    df = df_ibh[["nombre", "val_suelo"]].copy()
    df = df.merge(df_ose, on="nombre", how="outer")
    df = df.merge(df_gems, on="nombre", how="outer")
    df = df.merge(df_precip, on="nombre", how="outer")

    df["pct_ose_norm"] = _minmax(df["pct_ose"])
    df["val_gems_norm"] = _minmax(df["val_gems"])
    df["pct_contam"] = df[["pct_ose_norm", "val_gems_norm"]].mean(axis=1, skipna=True)

    p66_contam = df["pct_contam"].quantile(0.66)
    p66_precip = df["val_precip"].quantile(0.66)
    p33_suelo = df["val_suelo"].quantile(0.33)

    df["condicion_contam"] = df["pct_contam"].notna() & (df["pct_contam"] > p66_contam)
    df["condicion_precip"] = df["val_precip"].notna() & (df["val_precip"] > p66_precip)
    df["condicion_suelo"] = df["val_suelo"].notna() & (df["val_suelo"] < p33_suelo)

    df["score"] = (
        df["condicion_contam"].astype(int)
        + df["condicion_precip"].astype(int)
        + df["condicion_suelo"].astype(int)
    )

    return df[[
        "nombre", "score",
        "condicion_contam", "condicion_precip", "condicion_suelo",
        "pct_ose", "val_gems", "val_precip", "val_suelo",
    ]].dropna(subset=["nombre"]).reset_index(drop=True)
