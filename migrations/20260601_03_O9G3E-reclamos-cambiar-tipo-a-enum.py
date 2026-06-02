"""
reclamos cambiar tipo a enum
"""

from yoyo import step

__depends__ = {'20260601_02_Y1Js1-enum-tipo-reclamo'}

steps = [
    step("""--sql
         ALTER TABLE reclamosose
		 ALTER COLUMN tipo_reclamo TYPE reclamo_ose_tipo
         USING tipo_reclamo::reclamo_ose_tipo;
		 """)
]
