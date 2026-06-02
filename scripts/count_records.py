import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env.local")

from db import get_postgres_conn, get_mongo_conn

PG_TABLES = [
    "erosion_cuenca",
    "erosion_suelos",
    "gemsparams",
    "oseparam",
    "paraminumet",
    "puntomedicion",
    "reclamosose",
    "registrotempprec",
]


def count_postgres():
    conn = get_postgres_conn()
    cur = conn.cursor()
    results = []
    for table in PG_TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        results.append((table, cur.fetchone()[0]))
    conn.close()
    return results


def count_mongo():
    db = get_mongo_conn()
    results = []
    for name in sorted(db.list_collection_names()):
        results.append((name, db[name].count_documents({})))
    return results


def print_block(title, rows):
    width = max(len(name) for name, _ in rows)
    print(f"\n{title}")
    for name, count in rows:
        print(f"  {name:<{width}}  {count:>10,}")
    total = sum(c for _, c in rows)
    print(f"  {'TOTAL':<{width}}  {total:>10,}")


if __name__ == "__main__":
    print_block("PostgreSQL", count_postgres())
    print_block("MongoDB",    count_mongo())
    print()
