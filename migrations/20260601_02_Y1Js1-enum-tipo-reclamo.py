"""
enum tipo reclamo
"""

from yoyo import step

__depends__ = {'20260531_01_HYJp5-tabla-precipitaciones', '20260601_01_rLAmP-tabla-reclamos'}

steps = [
    step("""--sql
    CREATE TYPE reclamo_ose_tipo AS ENUM (
        'ALTO_CONSUMO',
        'DATOS_ERRONEOS_CONTRATO',
        'DENUNCIA_NOTIFICACION_FACTURAS',
        'DENUNCIA_NOTIFICACION_FACTURA_MAIL',
        'ERROR_LECTURA',
        'ERROR_TARIFA',
        'ERROR_ESTIMACION',
        'OTROS_AJUSTES_FACTURACION',
        'RETRASO_CONEXION_NUEVA',
        'QUEJAS_SUGERENCIAS',
        'VARIOS',
        'WS_GENERACION_AVISOS'
    )
    """)
]
