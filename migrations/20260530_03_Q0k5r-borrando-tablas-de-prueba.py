"""
borrando tablas de prueba
"""

from yoyo import step

__depends__ = {'20260530_02_MAfIh-cambiando-value-en-gems-params'}

steps = [
    step("""--sql
    DROP TABLE ropas;
	DROP TABLE usuarios;
""")
]
