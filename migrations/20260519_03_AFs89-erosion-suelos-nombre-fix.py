"""
erosion suelos nombre fix
"""

from yoyo import step

__depends__ = {'20260519_02_4id5x-nueva-tabla-erosion-suelos'}

steps = [
    step("""--sql
    ALTER TABLE erosionsuelos RENAME to erosion_suelos;
    """)
]
