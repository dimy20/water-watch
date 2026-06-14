import pandas as pd

from etl.inumet.pre_processing import pre_process_humedad_relativa, pre_process_precipitacion


def test_pre_process_precipitacion_descarta_nulos():
    df = pd.DataFrame({
        "fecha": ["2020-01-01", None, "2020-01-03"],
        "estacion_id": [" Rivera ", "Salto", "Artigas"],
        "precip_horario": [1.5, 2.0, None],
    })

    resultado = pre_process_precipitacion(df)

    assert len(resultado) == 1
    fila = resultado.iloc[0]
    assert fila["estacion_id"] == "Rivera"
    assert fila["fecha"] == pd.Timestamp("2020-01-01")
    assert fila["precip_horario"] == 1.5


def test_pre_process_precipitacion_descarta_valores_no_numericos():
    df = pd.DataFrame({
        "fecha": ["2020-01-01", "2020-01-02"],
        "estacion_id": ["Rivera", "Salto"],
        "precip_horario": [1.5, "no_numerico"],
    })

    resultado = pre_process_precipitacion(df)

    assert len(resultado) == 1
    assert resultado.iloc[0]["estacion_id"] == "Rivera"


def test_pre_process_precipitacion_tipos_resultantes():
    df = pd.DataFrame({
        "fecha": ["2020-01-01"],
        "estacion_id": ["Rivera"],
        "precip_horario": ["3.2"],
    })

    resultado = pre_process_precipitacion(df)

    assert pd.api.types.is_datetime64_any_dtype(resultado["fecha"])
    assert pd.api.types.is_numeric_dtype(resultado["precip_horario"])
    assert resultado.iloc[0]["precip_horario"] == 3.2


def test_pre_process_humedad_relativa_descarta_nulos():
    df = pd.DataFrame({
        "fecha": ["2020-01-01", "2020-01-02"],
        "estacion_id": ["Rivera", " Salto "],
        "hum_relativa": [None, 80.0],
    })

    resultado = pre_process_humedad_relativa(df)

    assert len(resultado) == 1
    fila = resultado.iloc[0]
    assert fila["estacion_id"] == "Salto"
    assert fila["hum_relativa"] == 80.0


def test_pre_process_humedad_relativa_tipos_resultantes():
    df = pd.DataFrame({
        "fecha": ["2020-01-01"],
        "estacion_id": ["Rivera"],
        "hum_relativa": ["75.5"],
    })

    resultado = pre_process_humedad_relativa(df)

    assert pd.api.types.is_datetime64_any_dtype(resultado["fecha"])
    assert pd.api.types.is_numeric_dtype(resultado["hum_relativa"])
    assert resultado.iloc[0]["hum_relativa"] == 75.5
