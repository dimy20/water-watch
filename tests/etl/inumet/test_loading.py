import pandas as pd

from etl.inumet.loading import crear_fila_param_inumet
from etl.utils import create_id


def test_crear_fila_param_inumet_estructura():
    location_id = create_id("Rivera", -30.9, -55.5)
    fecha = pd.Timestamp("2020-01-01 10:00:00")

    fila = crear_fila_param_inumet(location_id, fecha, 3.2, "PRECIP_HORARIA")

    param_id, loc_id, fecha_inicio, fecha_fin, value, code, granularidad = fila
    assert loc_id == location_id
    assert fecha_inicio == fecha
    assert fecha_fin == fecha + pd.Timedelta(hours=1)
    assert value == 3.2
    assert code == "PRECIP_HORARIA"
    assert granularidad == "HORA"


def test_crear_fila_param_inumet_id_determinista():
    location_id = create_id("Rivera", -30.9, -55.5)
    fecha = pd.Timestamp("2020-01-01 10:00:00")

    fila_1 = crear_fila_param_inumet(location_id, fecha, 3.2, "PRECIP_HORARIA")
    fila_2 = crear_fila_param_inumet(location_id, fecha, 3.2, "PRECIP_HORARIA")

    assert fila_1[0] == fila_2[0]


def test_crear_fila_param_inumet_id_cambia_con_fecha_o_code():
    location_id = create_id("Rivera", -30.9, -55.5)
    fecha = pd.Timestamp("2020-01-01 10:00:00")

    fila_base = crear_fila_param_inumet(location_id, fecha, 3.2, "PRECIP_HORARIA")
    fila_otra_fecha = crear_fila_param_inumet(location_id, fecha + pd.Timedelta(hours=1), 3.2, "PRECIP_HORARIA")
    fila_otro_code = crear_fila_param_inumet(location_id, fecha, 3.2, "HUM_RELATIVA")

    assert fila_base[0] != fila_otra_fecha[0]
    assert fila_base[0] != fila_otro_code[0]
