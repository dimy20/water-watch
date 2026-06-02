import unicodedata
import pandas as pd

COLS_KEEP = [
    "region",
    "departamento",
    "fecha_ingreso",
    "tipo_reclamo_comercial",
    "id_reclamo_comercial_m",
]

#tabla de normalizacion de tipos de reclamos a enum

RECLAMOS_MAP = {
    "Alto Consumo": "ALTO_CONSUMO",
    "Alto Consumo (Social)": "ALTO_CONSUMO",
    "Alto Consumo Web": "ALTO_CONSUMO",

    "Datos Erróneos de contrato": "DATOS_ERRONEOS_CONTRATO",
    "Datos ErrÃ³neos de contrato": "DATOS_ERRONEOS_CONTRATO",

    "Denuncia de Notificación de facturas": "DENUNCIA_NOTIFICACION_FACTURAS",
    "Denuncia de NotificaciÃ³n de facturas": "DENUNCIA_NOTIFICACION_FACTURAS",

    "Denuncia de Notificación Factura vía mail": "DENUNCIA_NOTIFICACION_FACTURA_MAIL",
    "Denuncia de NotificaciÃ³n Factura vÃ­a mail": "DENUNCIA_NOTIFICACION_FACTURA_MAIL",

    "Error de Lectura": "ERROR_LECTURA",
    "Error de Lectura (Social)": "ERROR_LECTURA",
    "Error de Lectura Web": "ERROR_LECTURA",

    "Error de Tarifa": "ERROR_TARIFA",
    "Error de Tarifa  (Social)": "ERROR_TARIFA",
    "Error de Tarifa Web": "ERROR_TARIFA",

    "Error en Estimación": "ERROR_ESTIMACION",
    "Error en Estimación (Social)": "ERROR_ESTIMACION",
    "Error en EstimaciÃ³n": "ERROR_ESTIMACION",
    "Error en EstimaciÃ³n (Social)": "ERROR_ESTIMACION",

    "Otros Ajustes de Facturación": "OTROS_AJUSTES_FACTURACION",
    "Otros Ajustes de Facturación (Social)": "OTROS_AJUSTES_FACTURACION",
    "Otros Ajustes de FacturaciÃ³n": "OTROS_AJUSTES_FACTURACION",
    "Otros Ajustes de FacturaciÃ³n (Social)": "OTROS_AJUSTES_FACTURACION",

    "Retraso de Conexión Nueva": "RETRASO_CONEXION_NUEVA",
    "Retraso de Conexión Nueva (Social)": "RETRASO_CONEXION_NUEVA",
    "Retraso de ConexiÃ³n Nueva": "RETRASO_CONEXION_NUEVA",
    "Retraso de ConexiÃ³n Nueva (Social)": "RETRASO_CONEXION_NUEVA",

    "Quejas y Sugerencias": "QUEJAS_SUGERENCIAS",
    "Quejas y Sugerencias Web": "QUEJAS_SUGERENCIAS",

    "Varios": "VARIOS",
    "Varios (Social )": "VARIOS",

    "WS Generación de Avisos": "WS_GENERACION_AVISOS",
    "WS GeneraciÃ³n de Avisos": "WS_GENERACION_AVISOS",
}


def normalizar_nombre(s: str) -> str:
    s = s.lower().strip()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def pre_process(df: pd.DataFrame) -> pd.DataFrame:
    df = df[[c for c in COLS_KEEP if c in df.columns]].copy()

    df = df[df["departamento"] != "SIN DATOS"]

    df["fecha_inicio"] = pd.to_datetime(df["fecha_ingreso"], errors="coerce")
    df["fecha_fin"] = df["fecha_inicio"] + pd.Timedelta(days=1)
    df = df.drop(columns=["fecha_ingreso"])

    df = df[df["fecha_inicio"].dt.year >= 2015]

    df["tipo_reclamo"] = df["tipo_reclamo_comercial"].map(RECLAMOS_MAP)
    df = df.drop(columns=["tipo_reclamo_comercial"])
    df = df.dropna(subset=["tipo_reclamo"])

    return df.reset_index(drop=True)
