import pandas as pd


def get_estaciones_por_departamento(mongo_db, departamento_id) -> list:
    depto = mongo_db["departamentos"].find_one({"_id": departamento_id}, {"geometry": 1})
    if not depto:
        return []
    estaciones = mongo_db["estaciones"].find(
        {"location": {"$geoWithin": {"$geometry": depto["geometry"]}}},
        {"_id": 1},
    )
    return [est["_id"] for est in estaciones]


def get_gems_evolucion(
    pg_conn,
    location_ids: list,
    anio_inicio: int,
    anio_fin: int,
    code: str,
) -> pd.DataFrame:
    if not location_ids:
        return pd.DataFrame(columns=["periodo", "valor_medio", "valor_min", "valor_max", "n_mediciones"])
    sql = """
        SELECT
            DATE_TRUNC('month', fecha_inicio) AS periodo,
            AVG(value)   AS valor_medio,
            MIN(value)   AS valor_min,
            MAX(value)   AS valor_max,
            COUNT(*)     AS n_mediciones
        FROM gemsparams
        WHERE location_id = ANY(%s)
          AND EXTRACT(YEAR FROM fecha_inicio) >= %s
          AND EXTRACT(YEAR FROM fecha_inicio) <= %s
          AND code = %s
          AND value IS NOT NULL
        GROUP BY periodo
        ORDER BY periodo
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (location_ids, anio_inicio, anio_fin, code))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["periodo", "valor_medio", "valor_min", "valor_max", "n_mediciones"])
    for col in ["valor_medio", "valor_min", "valor_max"]:
        df[col] = df[col].astype(float)
    return df
