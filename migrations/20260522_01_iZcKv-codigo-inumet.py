"""
codigo inumet
"""

from yoyo import step

__depends__ = {'20260519_04_rvafq-erosion-cuenca-nombre-fix'}

steps = [
    step("""
    CREATE TYPE codigo_inumet AS ENUM ('HUM_RELATIVA', 'PRECIP_HORARIA');
""")
]
