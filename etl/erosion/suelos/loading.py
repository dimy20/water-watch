import geopandas as gpd
from etl.erosion.suelos.logger import log
from db import get_mongo_conn, get_postgres_conn
from etl.erosion.suelos.pre_processing import pre_process
from etl.areas import crear_area_doc
from etl.utils import create_id
from pymongo import UpdateOne

FILENAME = "./data/Erodabilidad_de_suelos_(geojson_wgs84).geojson"

def crear_fila_erosion_suelo(area_id: str, grupo_coneat: str, perfil_modal: str, factor_k: float, taxonomia: str):
	erosion_id = create_id(area_id, grupo_coneat, perfil_modal, factor_k, taxonomia)
	new_fila = (erosion_id, area_id, grupo_coneat, perfil_modal, factor_k, taxonomia) 
	return new_fila

def load():
	# mongo connection
	mongo = get_mongo_conn()
	# posgresql connection
	sql_conn = get_postgres_conn()

	df = gpd.read_file(FILENAME)
	df = pre_process(df)

	operations = []

	rows = []
	
	for _, item in df.iterrows():
		grupo_coneat = item["gr_CONEAT"]
		perfil_modal = item["Perfil_mod"]
		factor_k 	 = item["Factor_K"]
		taxonomia    = item["Taxonomia_"]
		geometry     = item["geometry"]
	
		#mongo
		area_doc = crear_area_doc(geometry)

		operations.append(
			UpdateOne(
				{"_id": area_doc["_id"]},
				{"$setOnInsert": area_doc},
				upsert=True,
			)
		)
		#sql
		new_row = crear_fila_erosion_suelo(area_doc["_id"], grupo_coneat, perfil_modal, factor_k, taxonomia)
		rows.append(new_row)
	try:
		areas = mongo["areas"]
		result = areas.bulk_write(operations, ordered=False)
		log.info(f"MongoDB: Se inserto en areas {result.upserted_count} documentos")

		with sql_conn.cursor() as cur:
			cur.executemany(
				"""--sql
				INSERT INTO erosion_suelos (
					erosion_id,
					area_id, 
                    grupo_coneat,
					perfil_modal,
					factor_k, 
					taxonomia
				)
				VALUES (%s, %s, %s, %s, %s, %s)
				ON CONFLICT (erosion_id) DO NOTHING;
				""",
				rows
			)
			inserted_count = cur.rowcount
			
			log.info(f"PosgtreSQL: Se inserto en erosion_suelos {inserted_count} filas")
		
			sql_conn.commit()

	except Exception as e:
		sql_conn.rollback()
		log.error(f"Error insertando en datos de erosion suelos: {e}")
	finally:
		sql_conn.close()
