"""
cambiar area_id en erosion cuenca a uuid
"""

from yoyo import step

__depends__ = {'20260518_01_OhzRh-talba-erosion-cuenca'}

steps = [
    step("""--sql
    ALTER TABLE erosioncuenca
    ALTER COLUMN area_id TYPE UUID USING area_id::uuid,
	ALTER COLUMN area_id SET NOT NULL;
    """)
]
