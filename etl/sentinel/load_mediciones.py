import time
import pandas as pd
from db import get_mongo_conn, get_postgres_conn
from etl.utils import create_id
from etl.sentinel.params import DATA_FILE
from etl.sentinel.pre_processing import compute_index_series
from etl.sentinel.logger import log

INSERT_QUERY = """INSERT INTO sentinel_params(
    sentinel_param_id, location_id, code,
    fecha_inicio, fecha_fin, value, granularidad
) VALUES (%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT (sentinel_param_id) DO NOTHING;"""

def load(code: str):
    start = time.monotonic()
    mongo = get_mongo_conn()
    df = pd.read_csv(DATA_FILE)

    location_id_by_nombre = {
        doc["nombre"]: doc["_id"]
        for doc in mongo["sentinel_locations"].find(
            {"nombre": {"$in": df["Nombre"].tolist()}}, {"_id": 1, "nombre": 1}
        )
    }

    sql_conn = get_postgres_conn()
    with sql_conn.cursor() as cur:
        cur.execute("SELECT DISTINCT location_id FROM sentinel_params WHERE code = %s", (code,))
        ya_cargados = {location_id for (location_id,) in cur.fetchall()}
    sql_conn.close()

    total = len(df)
    total_inserted = 0
    skipped = 0

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        nombre = row["Nombre"]
        location_id = location_id_by_nombre.get(nombre)
        if location_id is None:
            log.warning(f"[{i}/{total}] {nombre}: sentinel_location no encontrada, se omite")
            skipped += 1
            continue

        if location_id in ya_cargados:
            log.info(f"[{i}/{total}] {nombre}: ya tiene mediciones {code} cargadas, se omite")
            continue

        log.info(f"[{i}/{total}] {nombre}: width={row['Width']} resolution={row['Resolution']}")
        serie = compute_index_series([row["Latitud"], row["Longitud"]], row["Width"], row["Resolution"], code)
        rows = [
            (create_id(location_id, code, fecha, fecha, valor, "DIA"), location_id, code, fecha, fecha, valor, "DIA")
            for fecha, valor in serie
        ]

        # se inserta por punto, con su propia conexion, para no perder el trabajo
        # ya calculado si se cae la conexion mas adelante
        sql_conn = get_postgres_conn()
        try:
            with sql_conn.cursor() as cur:
                cur.executemany(INSERT_QUERY, rows)
                log.info(f"[{i}/{total}] {nombre}: {cur.rowcount} mediciones insertadas")
                total_inserted += cur.rowcount
            sql_conn.commit()
        except Exception as e:
            sql_conn.rollback()
            log.error(f"[{i}/{total}] {nombre}: error insertando mediciones {code}: {e}")
        finally:
            sql_conn.close()

    elapsed = time.monotonic() - start
    log.info(f"PostgreSQL: {total_inserted} mediciones {code} insertadas en total, {skipped} puntos omitidos por location no encontrada (demoro {elapsed:.1f}s)")
