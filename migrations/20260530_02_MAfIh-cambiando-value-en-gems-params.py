"""
cambiando value en gems params
"""

from yoyo import step

__depends__ = {'20260530_01_lM7gf-gems-params'}

steps = [
    step("""--sql
    ALTER TABLE GemsParams
	ALTER COLUMN value DROP NOT NULL;
""")
]
