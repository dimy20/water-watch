"""
Uso:
    python scripts/sync_data.py    # sincroniza data/ desde CKAN (descarga lo nuevo/modificado)
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from db import get_postgres_conn
from etl import ckan_client
from etl.ckan_sources import SOURCES

DATA_DIR = ROOT / "data"


def _known_hash(cur, resource_id: str) -> str | None:
    cur.execute("SELECT hash FROM etl_file_state WHERE resource_id = %s", (resource_id,))
    row = cur.fetchone()
    return row[0] if row else None


def _upsert_file_state(cur, resource_id, package, modulo, hash_, archivo_local):
    cur.execute(
        """INSERT INTO etl_file_state (resource_id, package, modulo, hash, archivo_local, last_synced)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (resource_id) DO UPDATE SET
            hash = EXCLUDED.hash,
            archivo_local = EXCLUDED.archivo_local,
            last_synced = EXCLUDED.last_synced""",
        (resource_id, package, modulo, hash_, archivo_local, datetime.now(timezone.utc)),
    )


def sync() -> set[str]:
    """Descarga a data/ los recursos CKAN nuevos o modificados. Devuelve los modulos afectados."""
    modulos_afectados: set[str] = set()

    conn = get_postgres_conn()
    try:
        with conn.cursor() as cur:
            for package, (modulo, resolver) in SOURCES.items():
                resources = ckan_client.package_search(package)
                for resource in resources:
                    path = resolver(resource)
                    if path is None:
                        continue

                    resource_id = resource["id"]
                    hash_ = resource.get("hash", "")
                    if hash_ and hash_ == _known_hash(cur, resource_id):
                        continue

                    print(f"[{package}] {path} -> descargando (hash cambio o nuevo)")
                    contenido = ckan_client.download_resource(resource)
                    dest = DATA_DIR / path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(contenido)

                    _upsert_file_state(cur, resource_id, package, modulo, hash_, str(path))
                    modulos_afectados.add(modulo)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return modulos_afectados


def main():
    load_dotenv(ROOT / ".env.local")

    modulos_afectados = sync()
    if not modulos_afectados:
        print("Sin cambios.")
    else:
        print(f"Modulos afectados: {', '.join(sorted(modulos_afectados))}")
        print("Correr el pipeline ETL por separado (python main.py) para procesar los cambios.")


if __name__ == "__main__":
    main()
