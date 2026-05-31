"""
cambindo location_id to departamento_id
"""

from yoyo import step

__depends__ = {'20260530_04_T7T9E-nueva-table-ose'}

steps = [
    step("""--sql
    ALTER TABLE OSEParam
	RENAME COLUMN location_id TO departamento_id;
    """)
]
