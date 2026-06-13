"""
tabla sentinel_params para series NDCI de Sentinel-2
"""

from yoyo import step

__depends__ = {'20260610_01_e7gQp-tabla-etl-file-state'}

steps = [
    step("""--sql
    CREATE TABLE sentinel_params (
        sentinel_param_id UUID PRIMARY KEY,
        location_id UUID NOT NULL,
        code VARCHAR(50) NOT NULL,
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE NOT NULL,
        value FLOAT NOT NULL,
        granularidad granularidad_tipo NOT NULL,
        CHECK (fecha_inicio <= fecha_fin)
    );
    """)
]
