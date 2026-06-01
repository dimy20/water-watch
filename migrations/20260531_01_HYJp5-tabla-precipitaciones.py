"""
tabla precipitaciones
"""

from yoyo import step

__depends__ = {'20260530_05_87GGV-cambindo-location-id-to-departamento-id'}

steps = [
    step("""--sql
    CREATE TABLE RegistroTempPrec (
    registro_id UUID PRIMARY KEY,
    location_id UUID NOT NULL,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    temperatura_maxima FLOAT NOT NULL,
    temperatura_minima FLOAT NOT NULL,
    pluviometro FLOAT NOT NULL,
    granularidad granularidad_tipo NOT NULL,
    CHECK (fecha_inicio <= fecha_fin)
);

""")
]
