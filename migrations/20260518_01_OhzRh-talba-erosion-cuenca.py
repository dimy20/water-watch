"""
talba erosion cuenca
"""

from yoyo import step

__depends__ = {'20260515_04_gpIue-agregando-precio-a-ropas'}

steps = [
    step("""--sql
    CREATE TABLE IF NOT EXISTS ErosionCuenca (
        erosion_id UUID PRIMARY KEY,
        area_id TEXT NOT NULL UNIQUE,
        ponderacion_erosion DOUBLE PRECISION NOT NULL,
        cluster INTEGER NOT NULL
    );  
""")
]
