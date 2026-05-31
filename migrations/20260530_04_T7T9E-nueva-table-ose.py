"""
nueva table ose
"""

from yoyo import step

__depends__ = {'20260530_03_Q0k5r-borrando-tablas-de-prueba'}

steps = [
    step("""--sql
    CREATE TABLE OSEParam (
        ose_param_id UUID PRIMARY KEY,
        location_id UUID NOT NULL,
        code VARCHAR(50) NOT NULL,
        fecha_inicio TIMESTAMP NOT NULL,
        fecha_fin TIMESTAMP NOT NULL,
        value FLOAT,
        value_cat VARCHAR(50),
        granularidad granularidad_tipo NOT NULL
);
		 """)
]
