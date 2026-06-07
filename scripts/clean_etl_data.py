"""
Uso:
    python scripts/clean_etl_data.py              # limpia PostgreSQL y MongoDB
    python scripts/clean_etl_data.py postgres
    python scripts/clean_etl_data.py mongo
    python scripts/clean_etl_data.py --dry-run
    python scripts/clean_etl_data.py --yes        # no pide confirmacion

Variables en .env.local:
    ETL_DATABASE_URL, ETL_MONGO_URL

No elimina bases, tablas ni colecciones. Solo vacia datos ETL:
    - PostgreSQL: DELETE FROM por defecto, en orden inverso de dependencias
    - PostgreSQL opcional: TRUNCATE ... RESTART IDENTITY CASCADE
    - MongoDB: delete_many({})
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
GRAPH_FILE = ROOT / "etl" / "etl_graph.json"
MONGO_DB_NAME = "grp05db"
CONNECT_TIMEOUT_SECONDS = 10


PG_TABLE_BY_ETL_ID = {
    "erosion.cuencas": "erosion_cuenca",
    "erosion.suelos": "erosion_suelos",
    "inumet": "paraminumet",
    "bacteriologia_ose": "oseparam",
    "grillas": "puntomedicion",
    "precipitaciones.load_registros": "registrotempprec",
    "gems.load_mediciones": "gemsparams",
    "reclamos": "reclamosose",
}

MONGO_COLLECTION_BY_ETL_ID = {
    "departamentos": "departamentos",
    "estaciones": "estaciones",
    "grillas": "puntos_grilla",
    "erosion.cuencas": "areas",
    "erosion.suelos": "areas",
    "precipitaciones.load_estaciones": "estaciones",
    "gems.load_estaciones": "estaciones",
}


def load_graph():
    with GRAPH_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def topo_sort(graph):
    nodes = {item["id"]: set(item["requires"]) for item in graph}
    ordered = []

    while nodes:
        ready = sorted(node_id for node_id, deps in nodes.items() if not deps)
        if not ready:
            raise RuntimeError("etl_graph.json contiene dependencias circulares")

        ordered.extend(ready)
        for node_id in ready:
            del nodes[node_id]
        for deps in nodes.values():
            deps.difference_update(ready)

    return ordered


def unique_in_order(values):
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def cleaning_plan():
    # Para limpiar, se usa el orden inverso al de creacion/carga.
    reverse_etl_order = list(reversed(topo_sort(load_graph())))

    pg_tables = unique_in_order(
        PG_TABLE_BY_ETL_ID[node_id]
        for node_id in reverse_etl_order
        if node_id in PG_TABLE_BY_ETL_ID
    )
    mongo_collections = unique_in_order(
        MONGO_COLLECTION_BY_ETL_ID[node_id]
        for node_id in reverse_etl_order
        if node_id in MONGO_COLLECTION_BY_ETL_ID
    )

    return pg_tables, mongo_collections


def confirm_or_exit(target, pg_tables, mongo_collections):
    print("Se van a vaciar datos ETL. No se van a dropear bases, tablas ni colecciones.")
    if target in ("all", "postgres"):
        print(f"PostgreSQL: {', '.join(pg_tables)}")
    if target in ("all", "mongo"):
        print(f"MongoDB: {', '.join(mongo_collections)}")

    answer = input("Confirmar limpieza escribiendo 'limpiar': ").strip().lower()
    if answer != "limpiar":
        print("Cancelado.")
        sys.exit(1)


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


def show_postgres_activity(conn):
    print("  Sesiones activas en esta base:", flush=True)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT pid, usename, application_name, client_addr, state,
                   left(regexp_replace(query, '\\s+', ' ', 'g'), 120) AS query
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND pid <> pg_backend_pid()
            ORDER BY state, pid;
            """
        )
        rows = cur.fetchall()

    if not rows:
        print("    no hay otras sesiones visibles", flush=True)
        return

    for pid, user, app, client, state, query in rows:
        app = app or "-"
        client = client or "-"
        query = query or "-"
        print(f"    pid={pid} user={user} app={app} client={client} state={state} query={query}", flush=True)


def terminate_other_postgres_sessions(conn):
    print("  cerrando otras conexiones a PostgreSQL ...", flush=True)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT pid, pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND pid <> pg_backend_pid();
            """
        )
        rows = cur.fetchall()
    conn.commit()

    if not rows:
        print("  no habia otras conexiones para cerrar", flush=True)
        return

    for pid, terminated in rows:
        status = "cerrada" if terminated else "no se pudo cerrar"
        print(f"  pid {pid}: {status}", flush=True)


def run_postgres_delete(conn, tables):
    from psycopg import sql

    with conn.cursor() as cur:
        cur.execute(sql.SQL("SET lock_timeout = {}").format(sql.Literal("10s")))
        cur.execute(sql.SQL("SET statement_timeout = {}").format(sql.Literal("5min")))

    conn.commit()

    for table in tables:
        print(f"  borrando {table} ...", flush=True)
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table)))
            deleted = cur.rowcount
        conn.commit()
        print(f"  OK {table}: {deleted} filas borradas", flush=True)


def run_postgres_truncate(conn, tables, lock_timeout_seconds):
    from psycopg import sql

    with conn.cursor() as cur:
        cur.execute(sql.SQL("SET lock_timeout = {}").format(sql.Literal(f"{lock_timeout_seconds}s")))
        cur.execute(sql.SQL("SET statement_timeout = {}").format(sql.Literal("5min")))
        cur.execute(
            sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(", ").join(sql.Identifier(table) for table in tables)
            )
        )
    conn.commit()


def clean_postgres(tables, method="delete", dry_run=False, force_locks=False):
    if not tables:
        return

    print("\nPostgreSQL", flush=True)
    if dry_run:
        for table in tables:
            print(f"  DRY RUN {method} {table}", flush=True)
        return

    conn = get_postgres_conn()
    try:
        if method == "delete":
            print("  usando DELETE FROM para evitar locks exclusivos de TRUNCATE", flush=True)
            run_postgres_delete(conn, tables)
        else:
            print(f"  truncando tablas: {', '.join(tables)} ...", flush=True)
            run_postgres_truncate(conn, tables, lock_timeout_seconds=10)
        print("  OK PostgreSQL: tablas ETL vaciadas", flush=True)
    except Exception as e:
        conn.rollback()
        if getattr(e, "sqlstate", None) == "55P03":
            print(f"  ERROR: PostgreSQL esta esperando locks y no pudo ejecutar {method.upper()}.", flush=True)
            show_postgres_activity(conn)
            if force_locks:
                terminate_other_postgres_sessions(conn)
                print(f"  reintentando {method.upper()} ...", flush=True)
                if method == "delete":
                    run_postgres_delete(conn, tables)
                else:
                    run_postgres_truncate(conn, tables, lock_timeout_seconds=30)
                print("  OK PostgreSQL: tablas ETL vaciadas", flush=True)
                return
            print("  Cierre Streamlit/ETL/pgAdmin u otras terminales que usen la base y vuelva a correr.", flush=True)
            print("  Alternativas:", flush=True)
            print("    python scripts/clean_etl_data.py postgres", flush=True)
            print("    python scripts/clean_etl_data.py postgres --postgres-method truncate --force-postgres-locks", flush=True)
            sys.exit(1)
        print(f"  ERROR PostgreSQL: {e}", flush=True)
        sys.exit(1)
    finally:
        conn.close()


def clean_mongo(collections, dry_run=False):
    if not collections:
        return

    print("\nMongoDB", flush=True)
    db = get_mongo_db()

    try:
        for name in collections:
            if dry_run:
                print(f"  DRY RUN delete_many {{}} en {name}", flush=True)
                continue
            print(f"  limpiando {name} ...", flush=True)
            result = db[name].delete_many({})
            print(f"  OK {name}: {result.deleted_count} docs borrados", flush=True)
    except Exception as e:
        print(f"  ERROR MongoDB: {e}", flush=True)
        sys.exit(1)
    finally:
        db.client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", choices=["all", "postgres", "mongo"], default="all")
    parser.add_argument("--yes", action="store_true", help="No pedir confirmacion")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar que se limpiaria sin borrar")
    parser.add_argument(
        "--postgres-method",
        choices=["delete", "truncate"],
        default="delete",
        help="Metodo para limpiar PostgreSQL. delete evita locks exclusivos; truncate reinicia identidades.",
    )
    parser.add_argument(
        "--force-postgres-locks",
        action="store_true",
        help="Cerrar otras conexiones a PostgreSQL antes del TRUNCATE",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env.local")

    pg_tables, mongo_collections = cleaning_plan()

    if args.dry_run:
        print("DRY RUN: no se va a borrar nada.")
    elif not args.yes:
        confirm_or_exit(args.target, pg_tables, mongo_collections)

    if args.target in ("all", "postgres"):
        clean_postgres(
            pg_tables,
            method=args.postgres_method,
            dry_run=args.dry_run,
            force_locks=args.force_postgres_locks,
        )
    if args.target in ("all", "mongo"):
        clean_mongo(mongo_collections, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
