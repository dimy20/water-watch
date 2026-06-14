import pandas as pd

from etl.bacteriologia_ose.pre_processing import normalizar_nombre, pre_process


def test_normalizar_nombre_quita_acentos_y_pasa_a_minusculas():
    assert normalizar_nombre("Río Negro") == "rio negro"


def test_normalizar_nombre_quita_espacios_extremos():
    assert normalizar_nombre("  Montevideo  ") == "montevideo"


def _df_base():
    return pd.DataFrame({
        "area_analisis": ["microbiologia", "microbiologia"],
        "metodo": ["M1", "M2"],
        "laboratorio": ["Lab A", "Lab B"],
        "localidad": ["Montevideo", "Salto"],
        "parametro": ["coliformes", "coliformes"],
        "valor": ["5", "<1"],
        "trimestre": ["Trimestre 1", "Trimestre 3"],
        "año": [2023, 2023],
    })


def test_pre_process_elimina_columnas_de_drop():
    df = _df_base()

    resultado = pre_process(df)

    for col in ["area_analisis", "metodo", "laboratorio", "localidad"]:
        assert col not in resultado.columns


def test_pre_process_filtra_valor_menor_a_uno():
    df = _df_base()

    resultado = pre_process(df)

    assert len(resultado) == 1
    assert list(resultado["value_cat"]) == ["5"]


def test_pre_process_calcula_fechas_segun_trimestre():
    df = _df_base()

    resultado = pre_process(df)

    fila = resultado.iloc[0]
    assert fila["fecha_inicio"] == pd.Timestamp("2023-01-01")
    assert fila["fecha_fin"] == pd.Timestamp("2023-03-31")


def test_pre_process_renombra_columnas_y_agrega_metadata():
    df = _df_base()

    resultado = pre_process(df)

    assert "code" in resultado.columns
    assert "value_cat" in resultado.columns
    assert "parametro" not in resultado.columns
    assert "valor" not in resultado.columns
    assert resultado.iloc[0]["value"] is None
    assert resultado.iloc[0]["granularidad"] == "TRIMESTRE"


def test_pre_process_elimina_columnas_originales_de_periodo():
    df = _df_base()

    resultado = pre_process(df)

    assert "año" not in resultado.columns
    assert "trimestre" not in resultado.columns
