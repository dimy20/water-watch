import json
from etl.utils import crear_estacion_doc
from etl.estaciones.logger import log
from pymongo import UpdateOne
from db import get_mongo_conn

FILENAME_ESTACIONES = "./data/estaciones_inumet.json"

def load():
	try:
		with open(FILENAME_ESTACIONES, "r", encoding="utf-8") as f:
			estaciones_data = json.load(f)
	except FileNotFoundError:
		log.error(f"Archivo no encontrado: {FILENAME_ESTACIONES}")
		return
	except Exception as e:
		log.error(f"Error leyendo {FILENAME_ESTACIONES}: {e}")
		return

	log.info(f"Cargando {len(estaciones_data)} estaciones INUMET")

	ops = []
	for item in estaciones_data:
		doc = crear_estacion_doc(item["nombre"], item["latitud"], item["longitud"])
		ops.append(UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True))

	try:
		mongo = get_mongo_conn()
		result = mongo["estaciones"].bulk_write(ops, ordered=False)
		log.info(f"MongoDB: {result.upserted_count} estaciones insertadas, {result.matched_count} ya existían")
	except Exception as e:
		log.error(f"Error escribiendo en MongoDB: {e}")
