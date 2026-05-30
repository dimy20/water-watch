from typing import Literal
import pandas as pd
from db import get_mongo_conn, get_postgres_conn
from etl.utils import create_id
from etl.gems.logger import log
from etl.gems.params import IN_SITU, REMOTE_SENSING
from etl.gems.pre_processing import pre_process_gems_params

DATA_DIR = "./data/GFQA_v3"
PARAMS_BY_TIPO = {"in_situ": IN_SITU, "remote_sensing": REMOTE_SENSING}

def load(tipo: Literal["in_situ", "remote_sensing"]):
    if tipo not in PARAMS_BY_TIPO:
        raise RuntimeError(f"tipo solo puede ser {list(PARAMS_BY_TIPO.keys())}")

    params = PARAMS_BY_TIPO[tipo]
    mongo = get_mongo_conn()
    sql_conn = get_postgres_conn()

    estacion_id_by_nombre = {
        doc["nombre"]: doc["_id"]
        for doc in mongo["estaciones"].find(
            {"nombre": {"$regex": "^URY"}}, {"_id": 1, "nombre": 1}
        )
    }

    rows = []
    skipped = 0

    for code, filename in params.items():
        try:
            df = pd.read_csv(f"{DATA_DIR}/{filename}", encoding="ISO-8859-1", low_memory=False)
        except FileNotFoundError:
            log.error(f"Archivo no encontrado: {DATA_DIR}/{filename}")
            continue

        df = df[df["Parameter Code"] == code]
        df = df[df["GEMS Station Number"].str.startswith("URY", na=False)]
        df = df[pd.to_datetime(df["Sample Date"]).dt.year >= 2015]

        df = pre_process_gems_params(df)

        df["location_id"] = df["GEMS Station Number"].map(estacion_id_by_nombre)
        skipped += int(df["location_id"].isna().sum())
        df = df.dropna(subset=["location_id"])

        for _, row in df.iterrows():
            gems_param_id = create_id(
                row["location_id"],
                row["code"],
                row["fecha_inicio"],
                row["fecha_fin"],
                row["value"],
                row["unit"],
                row["data_quality"],
                row["depth"],
                row["granularidad"],
            )
            rows.append((
                gems_param_id,
                row["location_id"],
                row["code"],
                row["fecha_inicio"],
                row["fecha_fin"],
                row["value"],
                row["value_cat"],
                row["unit"],
                row["data_quality"],
                row["depth"],
                row["granularidad"],
            ))

    log.info(f"[{tipo}] {len(rows)} mediciones preparadas, {skipped} omitidas por estación no encontrada")

    try:
        with sql_conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO GemsParams(
                    gems_param_id, location_id, code,
                    fecha_inicio, fecha_fin, value, value_cat,
                    unit, data_quality, depth, granularidad
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (gems_param_id) DO NOTHING;""",
                rows,
            )
            log.info(f"[{tipo}] PostgreSQL: {cur.rowcount} filas insertadas")
            sql_conn.commit()
    except Exception as e:
        sql_conn.rollback()
        log.error(f"[{tipo}] Error insertando mediciones: {e}")
    finally:
        sql_conn.close()
