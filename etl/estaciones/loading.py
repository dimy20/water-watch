import json
from etl.utils import create_id
from pymongo import UpdateOne
from db import get_mongo_conn
#from logging import log

FILENAME_ESTACIONES = "./data/estaciones_inumet.json"

def crear_estacion_doc(nombre: str, latitud: float, longitud: float):
	location_id = create_id(nombre, latitud, longitud)
	estacion_doc = {
		"_id": location_id,
		"nombre": nombre,
		"latitud": latitud,
		"longitud": longitud,
	}
	return estacion_doc

def load():
	mongo = get_mongo_conn()

	with open(FILENAME_ESTACIONES, "r", encoding="utf-8") as f:
		estaciones_data = json.load(f)

	estaciones_operations = []

	for item in estaciones_data:
		nombre = item["nombre"]
		latitud = item["latitud"]
		longitud = item["longitud"]

		estacion_doc = crear_estacion_doc(nombre, latitud, longitud)

		estaciones_operations.append(
			UpdateOne(
				{"_id": estacion_doc["_id"]},
				{"$setOnInsert": estacion_doc},
				upsert=True,
			)
		)

	estaciones = mongo["estaciones"]
	result = estaciones.bulk_write(estaciones_operations, ordered=False)
	#log.info(f"MongoDB: Upsert estaciones {result.upserted_count} documentos")