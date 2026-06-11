"""
tabla etl_file_state para CDC de archivos CKAN
"""

from yoyo import step

__depends__ = {'20260601_03_O9G3E-reclamos-cambiar-tipo-a-enum'}

steps = [
    step("""--sql
    CREATE TABLE etl_file_state (
        resource_id   VARCHAR PRIMARY KEY,
        package       VARCHAR NOT NULL,
        modulo        VARCHAR NOT NULL,
        hash          VARCHAR NOT NULL,
        archivo_local VARCHAR NOT NULL,
        last_synced   TIMESTAMP NOT NULL
    );
    """)
]
