import pandas as pd


def get_reclamos_por_departamento(pg_conn, mongo_db, anio_inicio: int, anio_fin: int) -> pd.DataFrame:
    sql = """
        SELECT departamento_id, COUNT(*) AS total_reclamos
        FROM reclamosose
        WHERE EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY departamento_id
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (anio_inicio, anio_fin))
    rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=["nombre", "total_reclamos"])
    df = pd.DataFrame(rows, columns=["departamento_id", "total_reclamos"])
    uuids = df["departamento_id"].tolist()
    docs = mongo_db["departamentos"].find({"_id": {"$in": uuids}}, {"_id": 1, "nombre": 1})
    nombres = {d["_id"]: d["nombre"] for d in docs}
    df["nombre"] = df["departamento_id"].map(nombres)
    df["total_reclamos"] = df["total_reclamos"].astype(int)
    return df[["nombre", "total_reclamos"]].dropna(subset=["nombre"]).reset_index(drop=True)


def get_reclamos_trimestral(pg_conn, departamento_id, anio_inicio: int, anio_fin: int) -> pd.DataFrame:
    sql = """
        SELECT DATE_TRUNC('quarter', fecha_inicio) AS periodo, COUNT(*) AS n_reclamos
        FROM reclamosose
        WHERE departamento_id = %s
          AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY periodo
        ORDER BY periodo
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (departamento_id, anio_inicio, anio_fin))
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["periodo", "n_reclamos"])


def get_correlacion_reclamos_calidad(pg_conn, mongo_db, anio_inicio: int, anio_fin: int) -> pd.DataFrame:
    cur = pg_conn.cursor()

    cur.execute(
        """
        SELECT departamento_id, COUNT(*) AS total_reclamos
        FROM reclamosose
        WHERE EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
        GROUP BY departamento_id
        """,
        (anio_inicio, anio_fin),
    )
    reclamos = {row[0]: int(row[1]) for row in cur.fetchall()}

    cur.execute(
        """
        SELECT departamento_id,
               SUM(CASE WHEN value_cat = 'Presencia' THEN total ELSE 0 END) * 100.0 / SUM(total) AS pct_presencia
        FROM (
            SELECT departamento_id, value_cat, COUNT(*) AS total
            FROM oseparam
            WHERE code = 'COLIFORMES TOTALES'
              AND EXTRACT(YEAR FROM fecha_inicio) BETWEEN %s AND %s
            GROUP BY departamento_id, value_cat
        ) sub
        GROUP BY departamento_id
        """,
        (anio_inicio, anio_fin),
    )
    calidad = {row[0]: float(row[1]) for row in cur.fetchall()}

    ids_comunes = set(reclamos) & set(calidad)
    if not ids_comunes:
        return pd.DataFrame(columns=["nombre", "total_reclamos", "pct_presencia"])

    docs = mongo_db["departamentos"].find(
        {"_id": {"$in": list(ids_comunes)}},
        {"_id": 1, "nombre": 1},
    )
    nombres = {d["_id"]: d["nombre"] for d in docs}

    rows = [
        {
            "nombre": nombres.get(uid),
            "total_reclamos": reclamos[uid],
            "pct_presencia": calidad[uid],
        }
        for uid in ids_comunes
        if nombres.get(uid)
    ]
    return pd.DataFrame(rows).sort_values("total_reclamos", ascending=False).reset_index(drop=True)
