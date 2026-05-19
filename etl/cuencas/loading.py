import geopandas as gpd
from etl.cuencas.pre_processing import fix_nombres, cambiar_nombres
from db import get_mongo_conn, get_postgres_conn
from pymongo import InsertOne
from shapely.geometry import mapping
import uuid

from etl.cuencas.logger import log

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

		#mongo
		area_doc = {
			"_id":nombre,
			"geometry":mapping(geometry)
		}
		operations.append(
			InsertOne(
				area_doc
			)
		)

		#sql
		erosion_id = str(uuid.uuid4())
		area_id = item["NOMBRE"]
		ponderacion_erosion = item["A_pon_cuen"]
		cluster = item["Cluster"]
		
		new_row = (erosion_id, area_id, ponderacion_erosion, cluster)
		rows.append(new_row)

	
	try:
		areas = mongo["areas"]
		result = areas.bulk_write(operations)
		log.info(f"MongoSQL: Se inserto en areas {result.inserted_count} documentos")

		with sql_conn.cursor() as cur:
			cur.executemany(
				"""--sql
				INSERT INTO ErosionCuenca (
					erosion_id,
					area_id,
					ponderacion_erosion,
					cluster
				)
				VALUES (%s, %s, %s, %s)
				""",
				rows
			)
			inserted_count = cur.rowcount
			
			log.info(f"PosgtreSQL: Se inserto en ErosionCuenca {inserted_count} filas")
		
			sql_conn.commit()

	except Exception as e:
		sql_conn.rollback()
		log.error(f"PostgreSQL: Error insertando en ErosionCuenca: {e}")
	except Exception as e:
		log.error (f"MongoDB: Error al insertar en areas {e}")

	sql_conn.close()

	