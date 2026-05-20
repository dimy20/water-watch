"""
erosion cuenca nombre fix
"""

from yoyo import step

__depends__ = {'20260519_03_AFs89-erosion-suelos-nombre-fix'}

steps = [
    step("""--sql
    ALTER TABLE erosioncuenca RENAME TO erosion_cuenca;
""")
]
