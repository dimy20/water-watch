"""
Script de demo CDC para Sentinel-2.

Modos de uso:
    python scripts/cdc_sentinel.py --precompute [--nombre "Nombre"]
        Calcula NDCI via API STAC para locations nuevas en puntos_v1.csv,
        guarda cache en data/sentinel/cache/. No inserta en DB.
        Correr en casa antes de la presentacion (tarda varios minutos).

    python scripts/cdc_sentinel.py --cached [--nombre "Nombre"]
        Lee cache y carga en sentinel_params. El punto aparece en el dashboard.
        Correr en la presentacion (tarda segundos).

    python scripts/cdc_sentinel.py --reset [--nombre "Nombre"]
        Elimina de sentinel_params los registros cargados via --cached.
        Sin --nombre resetea todos los puntos cacheados.
        Prepara la re-ejecucion de --cached.

    python scripts/cdc_sentinel.py --agregar --nombre "Nombre" --lat -33.94 --lon -54.26
        Agrega un nuevo punto a puntos_v1.csv (width=0.05, resolution=10).
"""

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import init_logger  # noqa: F401 — activa logging para load_locations y compute_index_series
from dotenv import load_dotenv
load_dotenv(ROOT / ".env.local")

from db import get_mongo_conn, get_postgres_conn
from etl.sentinel.load_locations import load as load_locations
from etl.sentinel.params import DATA_FILE, CODE_NDCI
from etl.sentinel.pre_processing import compute_index_series
from etl.utils import create_id

CACHE_DIR = ROOT / "data" / "sentinel" / "cache"
DEFAULT_WIDTH = 0.03
DEFAULT_RESOLUTION = 10

INSERT_QUERY = """INSERT INTO sentinel_params(
    sentinel_param_id, location_id, code,
    fecha_inicio, fecha_fin, value, granularidad
) VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (sentinel_param_id) DO NOTHING;"""


def cache_path(nombre: str) -> Path:
    return CACHE_DIR / f"{nombre}_{CODE_NDCI}.csv"


def save_cache(nombre: str, serie: list[tuple]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(serie, columns=["fecha", "valor"])
    df.to_csv(cache_path(nombre), index=False)
    print(f"  cache guardado: {cache_path(nombre)} ({len(serie)} fechas)")


def load_cache(nombre: str) -> list[tuple]:
    path = cache_path(nombre)
    if not path.exists():
        raise FileNotFoundError(
            f"Cache no encontrado para '{nombre}': {path}\n"
            f"Correr --precompute primero."
        )
    df = pd.read_csv(path)
    return list(zip(pd.to_datetime(df["fecha"]).dt.date, df["valor"].astype(float)))


def get_ya_cargados() -> set:
    sql_conn = get_postgres_conn()
    try:
        with sql_conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT location_id FROM sentinel_params WHERE code = %s",
                (CODE_NDCI,),
            )
            return {row[0] for row in cur.fetchall()}
    finally:
        sql_conn.close()


def insertar_serie(nombre: str, location_id, serie: list[tuple]) -> int:
    rows = [
        (
            create_id(location_id, CODE_NDCI, fecha, fecha, valor, "DIA"),
            location_id,
            CODE_NDCI,
            fecha,
            fecha,
            valor,
            "DIA",
        )
        for fecha, valor in serie
    ]
    sql_conn = get_postgres_conn()
    try:
        with sql_conn.cursor() as cur:
            cur.executemany(INSERT_QUERY, rows)
            inserted = cur.rowcount
        sql_conn.commit()
        return inserted
    except Exception as e:
        sql_conn.rollback()
        print(f"  error insertando mediciones de '{nombre}': {e}")
        return 0
    finally:
        sql_conn.close()


def agregar_punto(nombre: str, lat: float, lon: float) -> None:
    csv_path = ROOT / "data" / "sentinel" / "puntos_v1.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        existentes = {row["Nombre"] for row in csv.DictReader(f)}
    if nombre in existentes:
        print(f"ERROR: '{nombre}' ya existe en puntos_v1.csv.")
        sys.exit(1)
    with open(csv_path, "rb") as f:
        f.seek(-1, 2)
        needs_newline = f.read(1) not in (b"\n", b"\r")

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        csv.writer(f).writerow([nombre, lat, lon, "", DEFAULT_WIDTH, DEFAULT_RESOLUTION])
    print(f"Agregado: {nombre} ({lat}, {lon}) width={DEFAULT_WIDTH} resolution={DEFAULT_RESOLUTION}")
    print(f"Siguiente paso: python scripts/cdc_sentinel.py --precompute --nombre \"{nombre}\"")


def reset_cached(nombre: str | None = None) -> None:
    if not CACHE_DIR.exists():
        print("No hay archivos de cache. Nada que resetear.")
        return

    if nombre is not None:
        cache_files = [CACHE_DIR / f"{nombre}_{CODE_NDCI}.csv"]
        if not cache_files[0].exists():
            print(f"No existe cache para '{nombre}': {cache_files[0]}")
            return
    else:
        cache_files = list(CACHE_DIR.glob(f"*_{CODE_NDCI}.csv"))
        if not cache_files:
            print("No hay archivos de cache NDCI. Nada que resetear.")
            return

    nombres = [f.stem.replace(f"_{CODE_NDCI}", "") for f in cache_files]
    print(f"Locations a resetear: {nombres}")

    mongo = get_mongo_conn()
    location_ids = [
        doc["_id"]
        for doc in mongo["sentinel_locations"].find(
            {"nombre": {"$in": nombres}}, {"_id": 1}
        )
    ]

    if not location_ids:
        print("No se encontraron location_ids en MongoDB para los nombres del cache.")
        return

    sql_conn = get_postgres_conn()
    try:
        with sql_conn.cursor() as cur:
            cur.execute(
                "DELETE FROM sentinel_params WHERE location_id = ANY(%s) AND code = %s",
                (location_ids, CODE_NDCI),
            )
            deleted = cur.rowcount
        sql_conn.commit()
        print(f"{deleted} registros eliminados de sentinel_params.")
        print("Listo para re-ejecutar --cached en la presentacion.")
    except Exception as e:
        sql_conn.rollback()
        print(f"Error al resetear: {e}")
    finally:
        sql_conn.close()


def main():
    parser = argparse.ArgumentParser(description="CDC Sentinel — demo de carga de nuevas localidades NDCI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--precompute",
        action="store_true",
        help="Calcula NDCI via API y guarda cache. No inserta en DB.",
    )
    group.add_argument(
        "--cached",
        action="store_true",
        help="Lee cache e inserta en sentinel_params. El punto aparece en el dashboard.",
    )
    group.add_argument(
        "--reset",
        action="store_true",
        help="Elimina de sentinel_params los registros cargados via --cached. Prepara la re-ejecucion.",
    )
    group.add_argument(
        "--agregar",
        action="store_true",
        help="Agrega un nuevo punto a puntos_v1.csv. Requiere --nombre, --lat y --lon.",
    )
    parser.add_argument("--nombre", type=str, default=None)
    parser.add_argument("--lat", type=float, default=None)
    parser.add_argument("--lon", type=float, default=None)
    args = parser.parse_args()

    if args.agregar:
        if not all([args.nombre, args.lat is not None, args.lon is not None]):
            parser.error("--agregar requiere --nombre, --lat y --lon.")
        agregar_punto(args.nombre, args.lat, args.lon)
        return

    if args.reset:
        reset_cached(nombre=args.nombre)
        return

    print("Paso 1: cargando locations en MongoDB...")
    load_locations()

    print("Paso 2: resolviendo location_ids desde MongoDB...")
    mongo = get_mongo_conn()
    df = pd.read_csv(DATA_FILE)
    location_id_by_nombre = {
        doc["nombre"]: doc["_id"]
        for doc in mongo["sentinel_locations"].find(
            {"nombre": {"$in": df["Nombre"].tolist()}}, {"_id": 1, "nombre": 1}
        )
    }

    print("Paso 3: detectando locations sin mediciones NDCI...")
    ya_cargados = get_ya_cargados()

    nuevas = [
        row for _, row in df.iterrows()
        if location_id_by_nombre.get(row["Nombre"]) not in ya_cargados
        and location_id_by_nombre.get(row["Nombre"]) is not None
        and (args.nombre is None or row["Nombre"] == args.nombre)
    ]

    if not nuevas:
        if args.nombre:
            print(f"'{args.nombre}' no encontrado, ya cargado, o no existe en el CSV.")
        else:
            print("Sin locations nuevas. Todas las locations ya tienen mediciones NDCI cargadas.")
        return

    print(f"{len(nuevas)} location(s) nueva(s): {[r['Nombre'] for r in nuevas]}")
    print()

    total_insertado = 0

    for row in nuevas:
        nombre = row["Nombre"]
        location_id = location_id_by_nombre[nombre]

        if args.precompute:
            print(f"[precompute] {nombre}: calculando NDCI via API (puede tardar varios minutos)...")
            serie = compute_index_series(
                [row["Latitud"], row["Longitud"]], row["Width"], row["Resolution"], CODE_NDCI
            )
            if not serie:
                print(f"  sin datos validos para '{nombre}', se omite")
                continue
            save_cache(nombre, serie)

        elif args.cached:
            print(f"[cached] {nombre}: leyendo cache...")
            try:
                serie = load_cache(nombre)
            except FileNotFoundError as e:
                print(f"  ERROR: {e}")
                sys.exit(1)
            print(f"  {len(serie)} fechas leidas del cache")
            inserted = insertar_serie(nombre, location_id, serie)
            print(f"  {inserted} mediciones insertadas en sentinel_params")
            total_insertado += inserted

    if args.cached:
        print(f"\nTotal: {total_insertado} mediciones NDCI insertadas.")
        print("Refrescar el dashboard para ver el nuevo punto en el mapa.")
    else:
        print("\nPrecomputo completado. El dashboard no fue modificado.")
        print("Correr --cached en la presentacion para insertar los datos.")


if __name__ == "__main__":
    main()
