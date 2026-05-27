import pandas as pd
from typing import Literal

from db import get_mongo_conn, get_postgres_conn
from etl.inumet.logger import log

from etl.inumet.pre_processing import (
    pre_process_humedad_relativa,
    pre_process_precipitacion
)

from etl.utils import create_id

CONFIG_BY_TIPO = {
    "precipitacion": {
        "filename": "./data/inumet_precipitacion_acumulada_horaria.csv",
        "pre_process": pre_process_precipitacion,
        "value_col": "precip_horario",
        "code": "PRECIP_HORARIA",
    },
    "humedad_relativa": {
        "filename": "./data/inumet_humedad_relativa.csv",
        "pre_process": pre_process_humedad_relativa,
        "value_col": "hum_relativa",
        "code": "HUM_RELATIVA",
    },
}

def crear_fila_param_inumet(location_id, fecha, value: float, code: str):
    granularidad = "HORA"
    param_id = create_id(location_id, fecha, code, granularidad)
    fecha_inicio = fecha
    fecha_fin = fecha + pd.Timedelta(hours=1)
    new_row = (param_id, location_id, fecha_inicio, fecha_fin, value, code, granularidad)
    return new_row


def load(tipo: Literal["humedad_relativa", "precipitacion"]):
    if tipo not in CONFIG_BY_TIPO:
        raise RuntimeError(f"tipo solo puede ser {list(CONFIG_BY_TIPO.keys())}")

    config = CONFIG_BY_TIPO[tipo]
    mongo = get_mongo_conn()
    sql_conn = get_postgres_conn()
    df = pd.read_csv(config["filename"], sep=";")
    df = config["pre_process"](df)

    rows = []
    skipped = 0

    nombres_estaciones = list(df["estacion_id"].unique())
    estacion_id_by_nombre = {}
    for nombre_estacion in nombres_estaciones:
        # encuentro la estacion con ese nombre en mongodb
        res = mongo["estaciones"].find_one({ 
            "nombre": nombre_estacion
        }, {"_id": 1})

        estacion_id = res["_id"]  # UUID
        estacion_id_by_nombre[nombre_estacion] = estacion_id # nombre -> uuid

    # ir a mon
    # agarrar todos los nombres de las estaciones antes [x]
    # ir a mongo y agarrar el  id de cada una
    # 
    for _, item in df.iterrows():
        nombre_estacion = item["estacion_id"]
        location_id = estacion_id_by_nombre[nombre_estacion]

        if not location_id:
            skipped += 1
            continue

        fecha = item["fecha"]
        
        value = float(item[config["value_col"]])
        rows.append(crear_fila_param_inumet(location_id, fecha, value, config["code"]))
    try:
        with sql_conn.cursor() as cur:
            cur.executemany(
                """--sql
                INSERT INTO ParamInumet(
                    param_id,
                    location_id,
                    fecha_inicio,
                    fecha_fin,
                    value,
                    code,
                    granularidad
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (param_id) DO NOTHING;
                """,
                rows,
            )
            inserted_count = cur.rowcount
            log.info(f"PostgreSQL: Se inserto en ParamInumet {inserted_count} filas")
            log.info(f"PostgreSQL: Filas omitidas por estacion no encontrada {skipped}")
            sql_conn.commit()

    except Exception as e:
        sql_conn.rollback()
        log.error(f"Error insertando en datos de inumet: {e}")
    finally:
        sql_conn.close()
