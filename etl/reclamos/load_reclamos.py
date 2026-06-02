import glob
import pandas as pd

from db import get_mongo_conn, get_postgres_conn
from etl.utils import create_id
from etl.reclamos.logger import log
from etl.reclamos.pre_processing import pre_process, normalizar_nombre

DATA_GLOB = "./data/reclamos/solicitudes_y_reclamos-comerciales_*.csv"


def load():
    files = sorted(glob.glob(DATA_GLOB))
    if not files:
        log.error(f"No se encontraron archivos en: {DATA_GLOB}")
        return

    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f, sep=";", encoding="latin1", low_memory=False))
        except Exception as e:
            log.error(f"Error leyendo {f}: {e}")
    if not dfs:
        return

    df = pre_process(pd.concat(dfs, ignore_index=True))
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
        reclamo_id = create_id(
            row["departamento_id"],
            row["tipo_reclamo"],
            row["region"],
            row["fecha_inicio"],
            row["fecha_fin"],
            row["id_reclamo_comercial_m"],
        )
        rows.append((
            reclamo_id,
            row["departamento_id"],
            row["tipo_reclamo"],
            row["region"],
            row["fecha_inicio"],
            row["fecha_fin"],
        ))

    sql_conn = get_postgres_conn()
    try:
        with sql_conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO ReclamosOSE (
                    reclamo_id, departamento_id, tipo_reclamo,
                    region, fecha_inicio, fecha_fin
                ) VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (reclamo_id) DO NOTHING;""",
                rows,
            )
            log.info(f"PostgreSQL: {cur.rowcount} filas insertadas")
            sql_conn.commit()
    except Exception as e:
        sql_conn.rollback()
        log.error(f"Error insertando en PostgreSQL: {e}")
    finally:
        sql_conn.close()
