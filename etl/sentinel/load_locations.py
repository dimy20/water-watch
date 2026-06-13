import pandas as pd
from shapely.geometry import mapping
from pymongo import UpdateOne
from db import get_mongo_conn
from etl.utils import create_id
from etl.sentinel.geo import make_bbox_polygon
from etl.sentinel.params import DATA_FILE
from etl.sentinel.logger import log

def crear_sentinel_location_doc(geometry, nombre: str) -> dict:
    return {
        "_id": create_id(geometry, nombre),
        "nombre": nombre,
        "geometry": mapping(geometry),
    }

def load():
    mongo = get_mongo_conn()
    df = pd.read_csv(DATA_FILE)

    operations = []
    for _, row in df.iterrows():
        geometry = make_bbox_polygon([row["Latitud"], row["Longitud"]], row["Width"])
        doc = crear_sentinel_location_doc(geometry, row["Nombre"])
        operations.append(
            UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True)
        )

    result = mongo["sentinel_locations"].bulk_write(operations, ordered=False)
    log.info(f"MongoDB: se insertaron {result.upserted_count} documentos en sentinel_locations")
