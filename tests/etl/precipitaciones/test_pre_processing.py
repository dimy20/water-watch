import pandas as pd

from etl.precipitaciones.pre_processing import pre_process


def test_pre_process_calcula_fecha_inicio_y_fin():
    df = pd.DataFrame({
        "fecha": ["2020-01-01"],
        "temperaturaMaxima": [30.0],
        "temperaturaMinima": [15.0],
        "pluviometro": [0.0],
    })

    resultado = pre_process(df)

    fila = resultado.iloc[0]
    assert fila["fecha_inicio"] == pd.Timestamp("2020-01-01 09:00:00")
    assert fila["fecha_fin"] == pd.Timestamp("2020-01-02 08:59:59")
    assert fila["granularidad"] == "DIA"
    assert "fecha" not in resultado.columns


def test_pre_process_descarta_nulos_en_temperatura_o_pluviometro():
    df = pd.DataFrame({
        "fecha": ["2020-01-01", "2020-01-02", "2020-01-03"],
        "temperaturaMaxima": [30.0, None, 28.0],
        "temperaturaMinima": [15.0, 14.0, None],
        "pluviometro": [0.0, 1.0, 2.0],
    })

    resultado = pre_process(df)

    assert len(resultado) == 1
    assert resultado.iloc[0]["fecha_inicio"] == pd.Timestamp("2020-01-01 09:00:00")


def test_pre_process_sin_nulos_conserva_todas_las_filas():
    df = pd.DataFrame({
        "fecha": ["2020-01-01", "2020-01-02"],
        "temperaturaMaxima": [30.0, 31.0],
        "temperaturaMinima": [15.0, 16.0],
        "pluviometro": [0.0, 5.5],
    })

    resultado = pre_process(df)

    assert len(resultado) == 2
