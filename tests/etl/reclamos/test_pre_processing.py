import pandas as pd

from etl.reclamos.pre_processing import normalizar_nombre, pre_process


def test_normalizar_nombre_quita_acentos_y_pasa_a_minusculas():
    assert normalizar_nombre("Río Negro") == "rio negro"


def _df_base():
    return pd.DataFrame({
        "region": ["Sur", "Sur", "Norte", "Sur", "Sur", "Sur"],
        "departamento": ["Montevideo", "Montevideo", "SIN DATOS", "Montevideo", "Montevideo", "Montevideo"],
        "fecha_ingreso": ["2023-01-15", "fecha invalida", "2023-02-01", "2010-01-01", "2023-03-01", "2023-04-01"],
        "tipo_reclamo_comercial": ["Alto Consumo", "Alto Consumo", "Alto Consumo", "Alto Consumo", "Alto Consumo", "Tipo Desconocido"],
        "id_reclamo_comercial_m": [1, 2, 3, 4, 5, 6],
        "columna_extra": ["x", "x", "x", "x", "x", "x"],
    })


def test_pre_process_conserva_solo_columnas_de_interes():
    df = _df_base()

    resultado = pre_process(df)

    assert "columna_extra" not in resultado.columns


def test_pre_process_descarta_sin_datos():
    df = _df_base()

    resultado = pre_process(df)

    assert "SIN DATOS" not in resultado["departamento"].values


def test_pre_process_descarta_fechas_invalidas():
    df = _df_base()

    resultado = pre_process(df)

    assert resultado["fecha_inicio"].isna().sum() == 0


def test_pre_process_calcula_fecha_fin_como_dia_siguiente():
    df = pd.DataFrame({
        "region": ["Sur"],
        "departamento": ["Montevideo"],
        "fecha_ingreso": ["2023-01-15"],
        "tipo_reclamo_comercial": ["Alto Consumo"],
        "id_reclamo_comercial_m": [1],
    })

    resultado = pre_process(df)

    assert resultado.iloc[0]["fecha_fin"] == pd.Timestamp("2023-01-16")


def test_pre_process_descarta_anteriores_a_2015():
    df = _df_base()

    resultado = pre_process(df)

    assert (resultado["fecha_inicio"].dt.year < 2015).sum() == 0


def test_pre_process_mapea_tipo_reclamo_y_descarta_no_mapeados():
    df = _df_base()

    resultado = pre_process(df)

    assert "tipo_reclamo_comercial" not in resultado.columns
    assert set(resultado["tipo_reclamo"].unique()) == {"ALTO_CONSUMO"}


def test_pre_process_reindexa_resultado():
    df = _df_base()

    resultado = pre_process(df)

    assert list(resultado.index) == list(range(len(resultado)))
