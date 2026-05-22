import geopandas as gpd
from etl.erosion.cuencas.pre_processing import fix_nombres, cambiar_nombres
from db import get_mongo_conn, get_postgres_conn
from pymongo import UpdateOne
import uuid
from etl.erosion.cuencas.logger import log
from etl.areas import crear_area_doc
from etl.utils import create_id

def crear_fila_erosion_cuenca(area_id: str, ponderacion_erosion:float, cluster:int):
	erosion_id = create_id(area_id, ponderacion_erosion, cluster)
	new_fila = (erosion_id, area_id, ponderacion_erosion, cluster) # <-------
	return new_fila

def load():
	# mongo connection
	mongo = get_mongo_conn()
	# posgresql connection
	sql_conn = get_postgres_conn()

	df = gpd.read_file("./data/erosion_de_99_cuencas_WGS84.geojsonl.json")
	new_names = fix_nombres(df)
	df = cambiar_nombres(df, new_names)

	operations = []

	rows = []
	
	for _, item in df.iterrows():
		nombre = item["NOMBRE"]
		cluster = item["Cluster"]
		geometry = item["geometry"]
		ponderacion_erosion = item["A_pon_cuen"]
		#mongo
		area_doc = crear_area_doc(geometry, nombre)

		operations.append(
			UpdateOne(
				{"_id": area_doc["_id"]},
				{"$setOnInsert": area_doc},
				upsert=True,
			)
		)

		new_row = crear_fila_erosion_cuenca(area_doc["_id"], ponderacion_erosion, cluster)
		rows.append(new_row)
	try:
		areas = mongo["areas"]
		result = areas.bulk_write(operations, ordered=False)
		log.info(f"MongoSQL: Se inserto en areas {result.inserted_count} documentos")
		with sql_conn.cursor() as cur:
			cur.executemany(
				"""--sql
				INSERT INTO erosion_cuenca(
					erosion_id,
					area_id, 
					ponderacion_erosion,
					cluster
				)
				VALUES (%s, %s, %s, %s)
				ON CONFLICT (erosion_id) DO NOTHING;
				""",
				rows
			)
			inserted_count = cur.rowcount
			
			log.info(f"PosgtreSQL: Se inserto en ErosionCuenca {inserted_count} filas")
		
			sql_conn.commit()

	except Exception as e:
		sql_conn.rollback()
		log.error(f"Error insertando en erosion cuencas : {e}")
	finally:
		sql_conn.close()
