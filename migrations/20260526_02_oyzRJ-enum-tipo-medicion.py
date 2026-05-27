"""
enum tipo medicion
"""

from yoyo import step

__depends__ = {'20260526_01_7WxM2-nueva-granularidad'}

steps = [
    step("""--sql
         CREATE TYPE tipo_medicion AS ENUM ('IBH', 'PAD', 'ANR')
    """)
]
