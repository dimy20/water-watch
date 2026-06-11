import pandas as pd
from db import get_mongo_conn, get_postgres_conn
from etl.utils import create_id
from etl.bacteriologia_ose.logger import log
from etl.bacteriologia_ose.pre_processing import pre_process, normalizar_nombre

DATA_FILE = "./data/calidad_de_agua_bacteriologia.csv"

def load():
    try:
        df = pd.read_csv(DATA_FILE, sep=";", encoding="utf-8")
    except FileNotFoundError:
        log.error(f"Archivo no encontrado: {DATA_FILE}")
        return
    except Exception as e:
        log.error(f"Error leyendo archivo: {e}")
        return

    df = pre_process(df)
    log.info(f"{len(df)} filas tras pre-procesamiento")

    mongo = get_mongo_conn()
    depto_id_by_nombre = {
        normalizar_nombre(doc["nombre"]): doc["_id"]
        for doc in mongo["departamentos"].find({}, {"_id": 1, "nombre": 1})
    }

    df["departamento_id"] = df["departamento"].map(
        lambda n: depto_id_by_nombre.get(normalizar_nombre(n))
    )
    skipped = int(df["departamento_id"].isna().sum())
    df = df.dropna(subset=["departamento_id"])
    log.info(f"{len(df)} filas con departamento_id, {skipped} omitidas")

    rows = []
    for _, row in df.iterrows():
        ose_param_id = create_id(
            row["departamento_id"],
            row["code"],
            row["fecha_inicio"],
            row["fecha_fin"],
            row["value_cat"],
            row["granularidad"],
            row["id_muestra_m"],
        )
        rows.append((
            ose_param_id,
            row["departamento_id"],
            row["code"],
            row["fecha_inicio"],
            row["fecha_fin"],
            row["value"],
            row["value_cat"],
            row["granularidad"],
        ))

    sql_conn = get_postgres_conn()
    try:
        with sql_conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO OSEParam(
                    ose_param_id, departamento_id, code,
                    fecha_inicio, fecha_fin, value, value_cat, granularidad
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (ose_param_id) DO NOTHING;""",
                rows,
            )
            log.info(f"PostgreSQL: {cur.rowcount} filas insertadas")
            sql_conn.commit()
    except Exception as e:
        sql_conn.rollback()
        log.error(f"Error insertando en PostgreSQL: {e}")
    finally:
        sql_conn.close()
