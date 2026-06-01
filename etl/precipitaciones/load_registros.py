from pathlib import Path

import pandas as pd

from db import get_mongo_conn, get_postgres_conn
from etl.precipitaciones.logger import log
from etl.precipitaciones.pre_processing import pre_process
from etl.utils import create_id

DATA_DIR = Path("./data/precipitaciones")

ESTACIONES = {
    "La Estanzuela": DATA_DIR / "La Estanzuela",
    "Las Brujas": DATA_DIR / "Las Brujas",
    "SaltoGrande": DATA_DIR / "SaltoGrande",
    "Tacuarembo": DATA_DIR / "Tacuarembo",
    "Treinta y Tres": DATA_DIR / "Treinta y Tres",
}


def _get_station_id(mongo, nombre: str):
    res = mongo["estaciones"].find_one({"nombre": nombre}, {"_id": 1})
    if not res:
        raise RuntimeError(
            f"Estación '{nombre}' no encontrada en MongoDB. Ejecutá load_estaciones primero."
        )
    return res["_id"]


def load():
    mongo = get_mongo_conn()
    sql_conn = get_postgres_conn()

    station_ids = {nombre: _get_station_id(mongo, nombre) for nombre in ESTACIONES}

    rows = []
    for nombre, estacion_dir in ESTACIONES.items():
        location_id = station_ids[nombre]
        csv_files = sorted(estacion_dir.glob("ppt_tmax_tmin_*.csv"))

        for csv_path in csv_files:
            df = pd.read_csv(csv_path)
            df = pre_process(df)

            for _, row in df.iterrows():
                registro_id = create_id(
                    location_id,
                    row["fecha_inicio"],
                    row["fecha_fin"],
                    row["temperaturaMaxima"],
                    row["temperaturaMinima"],
                    row["pluviometro"],
                    row["granularidad"],
                )
                rows.append((
                    registro_id,
                    location_id,
                    row["fecha_inicio"],
                    row["fecha_fin"],
                    float(row["temperaturaMaxima"]),
                    float(row["temperaturaMinima"]),
                    float(row["pluviometro"]),
                    row["granularidad"],
                ))

    log.info(f"Filas a insertar: {len(rows)}")

    try:
        with sql_conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO registrotempprec(
                    registro_id,
                    location_id,
                    fecha_inicio,
                    fecha_fin,
                    temperatura_maxima,
                    temperatura_minima,
                    pluviometro,
                    granularidad
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (registro_id) DO NOTHING;
                """,
                rows,
            )
            log.info(f"PostgreSQL: {cur.rowcount} filas insertadas en registrotempprec")
            sql_conn.commit()
    except Exception as e:
        sql_conn.rollback()
        log.error(f"Error insertando registros de temperatura/precipitación: {e}")
    finally:
        sql_conn.close()
