import os
from typing import Literal

import pandas as pd
from pymongo import UpdateOne

from db import get_mongo_conn, get_postgres_conn
from etl.grillas.logger import log
from etl.grillas.pre_processing import invertir_columnas
from etl.utils import create_id

DIR_BY_TIPO = {
    "IBH": "./data/grillas/ibh",
    "PAD": "./data/grillas/pad",
    "ANR": "./data/grillas/anr",
}

def load(tipo: Literal["IBH", "PAD", "ANR"]):
    if tipo not in DIR_BY_TIPO:
        raise RuntimeError(f"tipo solo puede ser {list(DIR_BY_TIPO.keys())}")

    mongo = get_mongo_conn()
    sql_conn = get_postgres_conn()

    punto_docs = {}
    medicion_rows = []

    directorio = DIR_BY_TIPO[tipo]
    for filename in sorted(os.listdir(directorio)):
        df = pd.read_csv(os.path.join(directorio, filename))
        df = invertir_columnas(df)

        for _, row in df.iterrows():
            lat = row["latitud"]
            lon = row["longitud"]
            punto_id = create_id(lat, lon)

            if punto_id not in punto_docs:
                punto_docs[punto_id] = {
                    "_id": punto_id,
                    "latitud": lat,
                    "longitud": lon,
                }

            medicion_id = create_id(punto_id, row["valor"], tipo, row["fecha_inicio"], row["fecha_fin"], "PERIODO")
            medicion_rows.append((
                medicion_id,
                punto_id,
                row["valor"],
                tipo,
                row["fecha_inicio"],
                row["fecha_fin"],
                "PERIODO",
            ))

    mongo_ops = [
        UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True)
        for doc in punto_docs.values()
    ]
    if mongo_ops:
        result = mongo["puntos_grilla"].bulk_write(mongo_ops)
        log.info(f"MongoDB: Se insertaron {result.upserted_count} puntos de grilla")

    try:
        with sql_conn.cursor() as cur:
            cur.executemany(
                """--sql
                INSERT INTO PuntoMedicion(
                    medicion_id,
                    punto_id,
                    value,
                    type,
                    fecha_inicio,
                    fecha_fin,
                    granularidad
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (medicion_id) DO NOTHING;
                """,
                medicion_rows,
            )
            inserted_count = cur.rowcount
            log.info(f"PostgreSQL: Se insertaron {inserted_count} mediciones {tipo} en PuntoMedicion")
            sql_conn.commit()
    except Exception as e:
        sql_conn.rollback()
        log.error(f"Error insertando mediciones {tipo}: {e}")
    finally:
        sql_conn.close()
