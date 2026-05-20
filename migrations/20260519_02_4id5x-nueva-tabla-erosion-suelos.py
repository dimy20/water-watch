"""
nueva tabla erosion suelos
"""

from yoyo import step

__depends__ = {'20260519_01_111af-cambiar-area-id-en-erosion-cuenca-a-uuid'}

steps = [
    step(
		"""--sql
        CREATE TABLE ErosionSuelos (
            erosion_id UUID PRIMARY KEY,
            area_id UUID NOT NULL,
            grupo_coneat VARCHAR NOT NULL,
            perfil_modal VARCHAR NOT NULL,
            factor_k FLOAT NOT NULL,
            taxonomia VARCHAR NOT NULL
        );
		"""
    )
]
