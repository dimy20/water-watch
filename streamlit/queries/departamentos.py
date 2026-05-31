import pandas as pd


def get_departamentos_con_datos(pg_conn, mongo_db) -> pd.DataFrame:
    cur = pg_conn.cursor()
    cur.execute("SELECT DISTINCT departamento_id FROM oseparam")
    uuids = [row[0] for row in cur.fetchall()]

    docs = mongo_db["departamentos"].find(
        {"_id": {"$in": uuids}},
        {"_id": 1, "nombre": 1},
    )
    rows = [{"departamento_id": d["_id"], "nombre": d["nombre"]} for d in docs]
    return pd.DataFrame(rows).sort_values("nombre").reset_index(drop=True)


def get_departamentos_geojson(mongo_db) -> dict:
    from shapely.geometry import shape, mapping

    docs = list(mongo_db["departamentos"].find({}, {"_id": 0, "nombre": 1, "geometry": 1}))
    features = []
    for doc in docs:
        geom = shape(doc["geometry"]).simplify(0.02, preserve_topology=True)
        features.append({
            "type": "Feature",
            "id": doc["nombre"],
            "properties": {"nombre": doc["nombre"]},
            "geometry": mapping(geom),
        })
    return {"type": "FeatureCollection", "features": features}


def get_pct_presencia_por_departamento(pg_conn, mongo_db) -> pd.DataFrame:
    sql = """
        SELECT
            departamento_id,
            SUM(CASE WHEN value_cat = 'Presencia' THEN total ELSE 0 END) * 100.0 / SUM(total) AS pct_presencia
        FROM (
            SELECT departamento_id, value_cat, COUNT(*) AS total
            FROM oseparam
            GROUP BY departamento_id, value_cat
        ) sub
        GROUP BY departamento_id
    """
    cur = pg_conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["departamento_id", "pct_presencia"])

    uuids = df["departamento_id"].tolist()
    docs = mongo_db["departamentos"].find({"_id": {"$in": uuids}}, {"_id": 1, "nombre": 1})
    nombres = {d["_id"]: d["nombre"] for d in docs}
    df["nombre"] = df["departamento_id"].map(nombres)
    df["pct_presencia"] = df["pct_presencia"].astype(float)
    return df[["nombre", "pct_presencia"]].dropna()
