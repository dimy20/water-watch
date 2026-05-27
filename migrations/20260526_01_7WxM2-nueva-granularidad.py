"""
nueva granularidad
"""

from yoyo import step

__depends__ = {'20260522_04_aot0Z-tabla-param-inumet'}

steps = [
    step("""--sql
        ALTER TYPE granularidad_tipo ADD VALUE 'PERIODO'
    """)
]
