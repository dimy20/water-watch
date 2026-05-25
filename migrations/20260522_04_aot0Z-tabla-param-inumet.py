"""
tabla param inumet
"""

from yoyo import step

__depends__ = {'20260522_03_8BqE0-tabla-param-inumet'}

steps = [
    step("""--sql
        CREATE TABLE ParamInumet ( 
        param_id UUID PRIMARY KEY, 
        location_id UUID NOT NULL, 
        fecha_inicio TIMESTAMP NOT NULL, 
        fecha_fin TIMESTAMP NOT NULL, 
        value DOUBLE PRECISION NOT NULL, 
        code codigo_inumet NOT NULL, 
        granularidad granularidad_tipo NOT NULL
    );
""")
]
