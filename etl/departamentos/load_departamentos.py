import json

from pymongo import UpdateOne

from db import get_mongo_conn
from etl.utils import create_id
from etl.departamentos.logger import log

DATA_FILE = "./data/departamentos.geojson"

def load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        log.error(f"Archivo no encontrado: {DATA_FILE}")
        return
    except Exception as e:
        log.error(f"Error leyendo {DATA_FILE}: {e}")
        return

    features = data.get("features", [])
    log.info(f"Cargando {len(features)} departamentos")

    ops = []
    for feature in features:
        props = feature["properties"]
        nombre = props["admlnm"]
        codigo = props["admlcd"]
        geometry = feature["geometry"]

        doc_id = create_id(nombre, codigo)
        doc = {
            "_id": doc_id,
            "nombre": nombre,
            "codigo": codigo,
            "geometry": geometry,
        }
        ops.append(UpdateOne({"_id": doc_id}, {"$setOnInsert": doc}, upsert=True))

    try:
        mongo = get_mongo_conn()
        result = mongo["departamentos"].bulk_write(ops, ordered=False)
        log.info(f"MongoDB: {result.upserted_count} departamentos insertados, {result.matched_count} ya existían")
    except Exception as e:
        log.error(f"Error escribiendo en MongoDB: {e}")
