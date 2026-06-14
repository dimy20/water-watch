import pandas as pd
from shapely.geometry import shape


TIPOS = {
    "IBH": "Índice de Humedad del Balance",
    "PAD": "Precipitación Acumulada Decádica",
    "ANR": "Agua No Retenida",
}


def get_hidrico_suelo_por_departamento(
    mongo_db, pg_conn, tipo: str, anio_inicio: int, anio_fin: int
) -> pd.DataFrame:
    departamentos = list(mongo_db["departamentos"].find({}, {"_id": 1, "nombre": 1, "geometry": 1}))

    point_map = {}
    representative_points = {}
    for depto in departamentos:
        punto_interior = shape(depto["geometry"]).representative_point()
        representative_points[depto["nombre"]] = [punto_interior.x, punto_interior.y]
        puntos = mongo_db["puntos_grilla"].find(
            {"location": {"$geoWithin": {"$geometry": depto["geometry"]}}},
            {"_id": 1},
        )
        ids = [p["_id"] for p in puntos]
        if not ids:
            cercano = mongo_db["puntos_grilla"].find_one(
                {
                    "location": {
                        "$nearSphere": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": [punto_interior.x, punto_interior.y],
                            }
                        }
                    }
                },
                {"_id": 1},
            )
            ids = [cercano["_id"]] if cercano else []
        if ids:
            point_map[depto["nombre"]] = ids

    if not point_map:
        return pd.DataFrame(columns=["nombre", "valor_medio"])

    all_ids = [pid for ids in point_map.values() for pid in ids]
    sql = """
        SELECT punto_id, AVG(value) AS valor_medio
        FROM puntomedicion
        WHERE punto_id = ANY(%s)
          AND type = %s
          AND EXTRACT(YEAR FROM fecha_inicio) >= %s
          AND EXTRACT(YEAR FROM fecha_inicio) <= %s
        GROUP BY punto_id
    """
    cur = pg_conn.cursor()
    cur.execute(sql, (all_ids, tipo, anio_inicio, anio_fin))
    punto_avg = {row[0]: float(row[1]) for row in cur.fetchall()}

    result = []
    for nombre, ids in point_map.items():
        valores = [punto_avg[i] for i in ids if i in punto_avg]
        if not valores:
            lon, lat = representative_points[nombre]
            cercanos = mongo_db["puntos_grilla"].find(
                {
                    "location": {
                        "$nearSphere": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat],
                            }
                        }
                    }
                },
                {"_id": 1},
            ).limit(12)
            ids_cercanos = [p["_id"] for p in cercanos]
            if ids_cercanos:
                cur.execute(sql, (ids_cercanos, tipo, anio_inicio, anio_fin))
                valores = [float(row[1]) for row in cur.fetchall()]
        if valores:
            result.append({"nombre": nombre, "valor_medio": sum(valores) / len(valores)})

    return pd.DataFrame(result)
