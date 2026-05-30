import pandas as pd
from pymongo import UpdateOne
from db import get_mongo_conn
from etl.utils import crear_estacion_doc
from etl.gems.logger import log

DATA_FILE = "./data/GFQA_v3/GEMStat_station_metadata.csv"

def load():
	try:
		df = pd.read_csv(DATA_FILE, encoding="ISO-8859-1")
	except FileNotFoundError:
		log.error(f"Archivo no encontrado: {DATA_FILE}")
		return
	except Exception as e:
		log.error(f"Error leyendo {DATA_FILE}: {e}")
		return

	uy = df[df["Country Name"] == "Uruguay"]
	log.info(f"Cargando {len(uy)} estaciones GEMS (Uruguay)")

	ops = []
	for _, row in uy.iterrows():
		doc = crear_estacion_doc(
			nombre=row["GEMS Station Number"],
			latitud=row["Latitude"],
			longitud=row["Longitude"],
		)
		ops.append(UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True))

	try:
		mongo = get_mongo_conn()
		result = mongo["estaciones"].bulk_write(ops, ordered=False)
		log.info(f"MongoDB: {result.upserted_count} estaciones insertadas, {result.matched_count} ya existían")
	except Exception as e:
		log.error(f"Error escribiendo en MongoDB: {e}")
