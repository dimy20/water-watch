"""
Conciliacion origen vs. cargado.

Para cada tarea del pipeline, lee el/los archivo(s) de origen y aplica el mismo
pre-procesamiento que usa el loader correspondiente (sin tocar la logica de carga
ni escribir nada), y compara ese conteo contra el conteo actual en destino
(PostgreSQL/MongoDB).

Es un script de solo lectura: no ejecuta el pipeline ni modifica datos.
"""

import argparse
import csv
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv

load_dotenv(ROOT / ".env.local")

from etl.bacteriologia_ose.load_bacteriologia import DATA_FILE as BACTERIOLOGIA_FILE
from etl.bacteriologia_ose.pre_processing import pre_process as pre_process_bacteriologia

from etl.departamentos.load_departamentos import DATA_FILE as DEPARTAMENTOS_FILE, _fix_geometry

from etl.erosion.suelos.loading import FILENAME as EROSION_SUELOS_FILE
from etl.erosion.suelos.pre_processing import pre_process as pre_process_erosion_suelos

from etl.estaciones.loading import FILENAME_ESTACIONES

from etl.grillas.loading import DIR_BY_TIPO as GRILLAS_DIR_BY_TIPO
from etl.grillas.pre_processing import invertir_columnas

from etl.inumet.loading import CONFIG_BY_TIPO as INUMET_CONFIG_BY_TIPO

from etl.precipitaciones.load_estaciones import ESTACIONES as PRECIPITACIONES_ESTACIONES
from etl.precipitaciones.pre_processing import pre_process as pre_process_precipitaciones

from etl.gems.load_estaciones import DATA_FILE as GEMS_ESTACIONES_FILE
from etl.gems.load_mediciones import DATA_DIR as GEMS_DATA_DIR, PARAMS_BY_TIPO as GEMS_PARAMS_BY_TIPO
from etl.gems.pre_processing import pre_process_gems_params

from etl.reclamos.load_reclamos import DATA_GLOB as RECLAMOS_DATA_GLOB
from etl.reclamos.pre_processing import pre_process as pre_process_reclamos

from etl.sentinel.params import DATA_FILE as SENTINEL_DATA_FILE

# No exportado por el loader, hardcodeado tal cual en etl/erosion/cuencas/loading.py
EROSION_CUENCAS_FILE = "./data/erosion_de_99_cuencas_WGS84.geojsonl.json"

MONGO_DB_NAME = "grp05db"
CONNECT_TIMEOUT_SECONDS = 10


def get_postgres_conn():
    import psycopg

    url = os.environ.get("ETL_DATABASE_URL")
    if not url:
        print("ERROR: Falta ETL_DATABASE_URL en .env.local")
        sys.exit(1)
    return psycopg.connect(url, connect_timeout=CONNECT_TIMEOUT_SECONDS)


def get_mongo_db():
    from pymongo import MongoClient

    url = os.environ.get("ETL_MONGO_URL")
    if not url:
        print("ERROR: Falta ETL_MONGO_URL en .env.local")
        sys.exit(1)

    client = MongoClient(
        url,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=CONNECT_TIMEOUT_SECONDS * 1000,
        connectTimeoutMS=CONNECT_TIMEOUT_SECONDS * 1000,
        socketTimeoutMS=60_000,
    )
    return client[MONGO_DB_NAME]


# ---------------------------------------------------------
# Lectores de origen (mismo pre-proceso que usa cada loader)
# ---------------------------------------------------------

def origen_departamentos():
    with open(DEPARTAMENTOS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = 0
    for feature in data.get("features", []):
        try:
            _fix_geometry(feature["geometry"])
            count += 1
        except ValueError:
            pass
    return count


def origen_estaciones_inumet():
    with open(FILENAME_ESTACIONES, "r", encoding="utf-8") as f:
        return len(json.load(f))


def origen_precipitaciones_estaciones():
    return len(PRECIPITACIONES_ESTACIONES)


def origen_gems_estaciones():
    df = pd.read_csv(GEMS_ESTACIONES_FILE, encoding="ISO-8859-1")
    return len(df[df["Country Name"] == "Uruguay"])


def origen_grillas(tipo):
    total = 0
    directorio = GRILLAS_DIR_BY_TIPO[tipo]
    for filename in sorted(os.listdir(directorio)):
        df = pd.read_csv(os.path.join(directorio, filename))
        df = invertir_columnas(df)
        total += len(df)
    return total


def origen_erosion_cuencas():
    df = gpd.read_file(EROSION_CUENCAS_FILE)
    return len(df)


def origen_erosion_suelos():
    df = gpd.read_file(EROSION_SUELOS_FILE)
    df = pre_process_erosion_suelos(df)
    return len(df)


def origen_inumet(tipo):
    config = INUMET_CONFIG_BY_TIPO[tipo]
    df = pd.read_csv(config["filename"], sep=";")
    df = config["pre_process"](df)
    return len(df)


def origen_bacteriologia():
    df = pd.read_csv(BACTERIOLOGIA_FILE, sep=";", encoding="utf-8")
    df = pre_process_bacteriologia(df)
    return len(df)


def origen_precipitaciones_registros():
    total = 0
    for estacion_dir in PRECIPITACIONES_ESTACIONES.values():
        for csv_path in sorted(estacion_dir.glob("ppt_tmax_tmin_*.csv")):
            df = pd.read_csv(csv_path)
            df = pre_process_precipitaciones(df)
            total += len(df)
    return total


def origen_gems_mediciones(tipo):
    params = GEMS_PARAMS_BY_TIPO[tipo]
    total = 0
    for code, filename in params.items():
        try:
            df = pd.read_csv(f"{GEMS_DATA_DIR}/{filename}", encoding="ISO-8859-1", low_memory=False)
        except FileNotFoundError:
            continue
        df = df[df["Parameter Code"] == code]
        df = df[df["GEMS Station Number"].str.startswith("URY", na=False)]
        df = df[pd.to_datetime(df["Sample Date"]).dt.year >= 2015]
        df = pre_process_gems_params(df)
        total += len(df)
    return total


def origen_reclamos():
    files = sorted(glob.glob(RECLAMOS_DATA_GLOB))
    dfs = [pd.read_csv(f, sep=";", encoding="latin1", low_memory=False) for f in files]
    df = pre_process_reclamos(pd.concat(dfs, ignore_index=True))
    return len(df)


def origen_sentinel_locations():
    df = pd.read_csv(SENTINEL_DATA_FILE)
    return len(df)


# ---------------------------------------------------------
# Conteo de destino
# ---------------------------------------------------------

def count_pg(conn, table):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


def count_mongo(db, collection):
    return db[collection].count_documents({})


# ---------------------------------------------------------
# Tareas con destino propio (comparacion 1:1)
# ---------------------------------------------------------

TAREAS_PROPIAS = [
    {
        "id": "departamentos",
        "origen": origen_departamentos,
        "destino": ("mongo", "departamentos"),
        "motivo": "-",
        "motivo_corto": "-",
    },
    {
        "id": "erosion.cuencas",
        "origen": origen_erosion_cuencas,
        "destino": ("postgres", "erosion_cuenca"),
        "motivo": "dedup por create_id (ON CONFLICT)",
        "motivo_corto": "dedup",
    },
    {
        "id": "erosion.suelos",
        "origen": origen_erosion_suelos,
        "destino": ("postgres", "erosion_suelos"),
        "motivo": "dedup por create_id (ON CONFLICT)",
        "motivo_corto": "dedup",
    },
    {
        "id": "bacteriologia_ose",
        "origen": origen_bacteriologia,
        "destino": ("postgres", "oseparam"),
        "motivo": "dedup por create_id (ON CONFLICT) + filas sin departamento_id mapeado se descartan tras el pre-proceso",
        "motivo_corto": "dedup + filas sin departamento",
    },
    {
        "id": "precipitaciones.registros",
        "origen": origen_precipitaciones_registros,
        "destino": ("postgres", "registrotempprec"),
        "motivo": "dedup por create_id (ON CONFLICT)",
        "motivo_corto": "dedup",
    },
    {
        "id": "reclamos",
        "origen": origen_reclamos,
        "destino": ("postgres", "reclamosose"),
        "motivo": "dedup por create_id (ON CONFLICT) + filas sin departamento_id mapeado se descartan tras el pre-proceso",
        "motivo_corto": "dedup + filas sin departamento",
    },
    {
        "id": "sentinel.locations",
        "origen": origen_sentinel_locations,
        "destino": ("mongo", "sentinel_locations"),
        "motivo": "dedup por create_id (upsert)",
        "motivo_corto": "dedup",
    },
]


# ---------------------------------------------------------
# Destinos compartidos por varias tareas
# ---------------------------------------------------------

DESTINOS_COMPARTIDOS = [
    {
        "destino": ("mongo", "estaciones"),
        "tareas": [
            ("estaciones.inumet", origen_estaciones_inumet),
            ("precipitaciones.estaciones", origen_precipitaciones_estaciones),
            ("gems.estaciones", origen_gems_estaciones),
        ],
        "motivo": "dedup por create_id(nombre, latitud, longitud); colisiones posibles si distintas fuentes comparten nombre/coordenadas",
        "motivo_corto": "compartido (inumet+precipitaciones+gems); dedup",
    },
    {
        "destino": ("mongo", "areas"),
        "tareas": [
            ("erosion.cuencas", origen_erosion_cuencas),
            ("erosion.suelos", origen_erosion_suelos),
        ],
        "motivo": "dedup por create_id(geometry, ...) (upsert)",
        "motivo_corto": "compartido (erosion cuencas+suelos); dedup",
    },
    {
        "destino": ("postgres", "paraminumet"),
        "tareas": [
            ("inumet.precipitacion", lambda: origen_inumet("precipitacion")),
            ("inumet.humedad_relativa", lambda: origen_inumet("humedad_relativa")),
        ],
        "motivo": "dedup por create_id (ON CONFLICT) + filas sin estacion encontrada en mongo.estaciones se omiten",
        "motivo_corto": "compartido (inumet precipitacion+humedad); dedup + lookup",
    },
    {
        "destino": ("postgres", "puntomedicion"),
        "tareas": [
            ("grillas.IBH", lambda: origen_grillas("IBH")),
            ("grillas.PAD", lambda: origen_grillas("PAD")),
            ("grillas.ANR", lambda: origen_grillas("ANR")),
        ],
        "motivo": "dedup por create_id (ON CONFLICT)",
        "motivo_corto": "compartido (grillas IBH+PAD+ANR); dedup",
    },
    {
        "destino": ("postgres", "gemsparams"),
        "tareas": [
            ("gems.in_situ", lambda: origen_gems_mediciones("in_situ")),
            ("gems.remote_sensing", lambda: origen_gems_mediciones("remote_sensing")),
        ],
        "motivo": "dedup por create_id (ON CONFLICT) + filas sin estacion URY encontrada se omiten",
        "motivo_corto": "compartido (gems in_situ+remote_sensing); dedup + lookup",
    },
    {
        "destino": ("postgres", "sentinel_params"),
        "tareas": [
            ("sentinel.ndci", None),
            ("sentinel.turbidez", None),
        ],
        "motivo": "no aplica: las series se calculan dinamicamente via Sentinel Hub API por punto/dia, no hay un conteo de origen estatico",
        "motivo_corto": "compartido (sentinel ndci+turbidez); origen N/A (dinamico)",
    },
]


# ---------------------------------------------------------
# Impresion
# ---------------------------------------------------------

def get_count(pg_conn, mongo_db, destino):
    tipo, nombre = destino
    if tipo == "postgres":
        return count_pg(pg_conn, nombre)
    return count_mongo(mongo_db, nombre)


NOTA_NEGATIVOS = (
    "(*) Diferencia negativa = cargado > origen: el destino tiene filas que el archivo de origen "
    "actual ya no genera (quedaron de una version anterior del archivo, reemplazada despues de la "
    "ultima carga). La carga es solo aditiva (ON CONFLICT/upsert, nunca borra), por lo que esas filas "
    "no se eliminan solas. No es un error de carga ni una perdida de datos: indica que data/ cambio "
    "despues de la ultima carga."
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        metavar="PATH",
        help="Ademas del reporte por consola, exporta una tabla resumida (fuente, origen, cargado, diferencia, motivo) a este archivo CSV.",
    )
    args = parser.parse_args()

    pg_conn = get_postgres_conn()
    mongo_db = get_mongo_db()

    print("=== Conciliacion origen vs. cargado ===\n")

    hay_negativos = False
    csv_rows = []

    print("-- Tareas con destino propio --\n")
    header = f"{'tarea':<28} {'origen':>10} {'cargado':>10} {'diferencia':>10}  destino                 motivo"
    print(header)
    print("-" * len(header))
    for tarea in TAREAS_PROPIAS:
        try:
            origen = tarea["origen"]()
        except FileNotFoundError as e:
            print(f"{tarea['id']:<28} {'N/A':>10}  (archivo de origen no encontrado: {e})")
            continue
        destino_tipo, destino_nombre = tarea["destino"]
        cargado = get_count(pg_conn, mongo_db, tarea["destino"])
        diferencia = origen - cargado
        destino_str = f"{destino_tipo}.{destino_nombre}"
        motivo = tarea["motivo"]
        motivo_corto = tarea["motivo_corto"]
        if diferencia < 0:
            motivo = f"{motivo} (*)"
            motivo_corto = f"{motivo_corto} (*)"
            hay_negativos = True
        print(f"{tarea['id']:<28} {origen:>10} {cargado:>10} {diferencia:>10}  {destino_str:<22}  {motivo}")
        csv_rows.append({
            "fuente": tarea["id"],
            "origen": origen,
            "cargado": cargado,
            "diferencia": diferencia,
            "motivo": motivo_corto,
        })

    print("\n-- Destinos compartidos por varias tareas --")
    for grupo in DESTINOS_COMPARTIDOS:
        destino_tipo, destino_nombre = grupo["destino"]
        cargado = get_count(pg_conn, mongo_db, grupo["destino"])
        print(f"\n{destino_tipo}.{destino_nombre}  (cargado={cargado})")
        suma_origenes = 0
        hay_na = False
        for tarea_id, origen_fn in grupo["tareas"]:
            if origen_fn is None:
                print(f"  - {tarea_id:<26} origen=N/A")
                hay_na = True
                continue
            try:
                origen = origen_fn()
            except FileNotFoundError as e:
                print(f"  - {tarea_id:<26} origen=N/A (archivo no encontrado: {e})")
                hay_na = True
                continue
            suma_origenes += origen
            print(f"  - {tarea_id:<26} origen={origen}")
        fuente_str = f"{destino_tipo}.{destino_nombre}"
        motivo_corto = grupo["motivo_corto"]
        if hay_na:
            print(f"  motivo: {grupo['motivo']}")
            csv_rows.append({
                "fuente": fuente_str,
                "origen": "N/A",
                "cargado": cargado,
                "diferencia": "N/A",
                "motivo": motivo_corto,
            })
        else:
            diferencia = suma_origenes - cargado
            motivo = grupo["motivo"]
            if diferencia < 0:
                motivo = f"{motivo} (*)"
                motivo_corto = f"{motivo_corto} (*)"
                hay_negativos = True
            print(f"  suma origenes={suma_origenes}  diferencia={diferencia}")
            print(f"  motivo: {motivo}")
            csv_rows.append({
                "fuente": fuente_str,
                "origen": suma_origenes,
                "cargado": cargado,
                "diferencia": diferencia,
                "motivo": motivo_corto,
            })

    if hay_negativos:
        print(f"\n{NOTA_NEGATIVOS}")

    pg_conn.close()
    print()

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fuente", "origen", "cargado", "diferencia", "motivo"])
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"CSV escrito en: {args.csv}")


if __name__ == "__main__":
    main()
