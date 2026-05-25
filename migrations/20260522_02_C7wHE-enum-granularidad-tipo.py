"""
enum granularidad tipo
"""

from yoyo import step

__depends__ = {'20260522_01_iZcKv-codigo-inumet'}

steps = [
    step("""

CREATE TYPE granularidad_tipo AS ENUM ('HORA', 'DIA', 'SEMANA', 'MES', 'TRIMESTRE', 'ANIO');


""")
]
