"""
nueva table punto medicion
"""

from yoyo import step

__depends__ = {'20260526_02_oyzRJ-enum-tipo-medicion'}

steps = [
    step("""--sql
    CREATE TABLE PuntoMedicion (
        medicion_id UUID PRIMARY KEY,
        punto_id UUID NOT NULL,
        value FLOAT NOT NULL,
        type tipo_medicion NOT NULL,
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE NOT NULL,
        granularidad granularidad_tipo NOT NULL
    );
    """)
]
