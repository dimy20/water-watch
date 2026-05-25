"""
tabla param inumet
"""

from yoyo import step

__depends__ = {'20260522_02_C7wHE-enum-granularidad-tipo'}

steps = [
    step("""
CREATE TYPE granularidad_tipo AS ENUM ('HORA', 'DIA', 'SEMANA', 'MES', 'TRIMESTRE', 'ANIO');
""")
]
