"""
gems params
"""

from yoyo import step

__depends__ = {'20260526_03_RVLjL-nueva-table-punto-medicion'}

steps = [
    step("""--sql
    
	CREATE TABLE GemsParams (
    gems_param_id UUID PRIMARY KEY,
    location_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,
    value_cat VARCHAR(50),
    unit VARCHAR(30),
    data_quality VARCHAR(30),
    depth FLOAT,
    granularidad granularidad_tipo NOT NULL,
    CHECK (fecha_inicio <= fecha_fin)
);	 	 """)
]
