"""
Indices para consultas
"""

from yoyo import step

__depends__ = {'20260613_01_nC4xT-tabla-sentinel-params'}

steps = [
    step(
        """CREATE INDEX IF NOT EXISTS idx_reclamosose_depto_fecha
ON reclamosose (departamento_id, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_oseparam_depto_code_fecha_valuecat
ON oseparam (departamento_id, code, fecha_inicio, value_cat);

CREATE INDEX IF NOT EXISTS idx_oseparam_code_fecha_depto_valuecat
ON oseparam (code, fecha_inicio, departamento_id, value_cat);

CREATE INDEX IF NOT EXISTS idx_gemsparams_location_code_fecha
ON gemsparams (location_id, code, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_gemsparams_code_location
ON gemsparams (code, location_id);

CREATE INDEX IF NOT EXISTS idx_puntomedicion_punto_type_fecha
ON puntomedicion (punto_id, type, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_registrotempprec_location_fecha
ON registrotempprec (location_id, fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_paraminumet_location_fecha
ON paraminumet (location_id, fecha_inicio);
""")
]
