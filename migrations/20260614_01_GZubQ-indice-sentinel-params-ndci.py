"""
indice sentinel params ndci
"""

from yoyo import step

__depends__ = {'20260613_02_GzU9C-indices-para-consultas'}

steps = [
    step("""--sql
    CREATE INDEX IF NOT EXISTS idx_sentinelparams_code_location_fecha
    ON sentinel_params (code, location_id, fecha_inicio);
    """)
]
