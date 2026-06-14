import calendar

import pandas as pd
import pytest

from etl.grillas.pre_processing import borrar_columnas, invertir_columnas, parse_date_column


def test_parse_date_column_periodo_1():
    fecha_inicio, fecha_fin = parse_date_column("2020_011")
    assert fecha_inicio == pd.Timestamp(2020, 1, 1, 0, 0, 0)
    assert fecha_fin == pd.Timestamp(2020, 1, 10, 23, 59, 59)


def test_parse_date_column_periodo_2():
    fecha_inicio, fecha_fin = parse_date_column("2020_012")
    assert fecha_inicio == pd.Timestamp(2020, 1, 11, 0, 0, 0)
    assert fecha_fin == pd.Timestamp(2020, 1, 20, 23, 59, 59)


def test_parse_date_column_periodo_3_mes_31_dias():
    fecha_inicio, fecha_fin = parse_date_column("2020_013")
    assert fecha_inicio == pd.Timestamp(2020, 1, 21, 0, 0, 0)
    assert fecha_fin == pd.Timestamp(2020, 1, 31, 23, 59, 59)


def test_parse_date_column_periodo_3_febrero_bisiesto():
    fecha_inicio, fecha_fin = parse_date_column("2020_023")
    assert calendar.isleap(2020)
    assert fecha_inicio == pd.Timestamp(2020, 2, 21, 0, 0, 0)
    assert fecha_fin == pd.Timestamp(2020, 2, 29, 23, 59, 59)


def test_parse_date_column_periodo_3_febrero_no_bisiesto():
    fecha_inicio, fecha_fin = parse_date_column("2021_023")
    assert not calendar.isleap(2021)
    assert fecha_inicio == pd.Timestamp(2021, 2, 21, 0, 0, 0)
    assert fecha_fin == pd.Timestamp(2021, 2, 28, 23, 59, 59)


def test_parse_date_column_periodo_invalido():
    with pytest.raises(ValueError):
        parse_date_column("2020_014")


def test_borrar_columnas_elimina_columnas_de_promedio():
    df = pd.DataFrame(columns=["Longitud", "Latitud", "id", "2020_011", "2020_012", "2020_013", "2020_010"])
    resultado = borrar_columnas(df)
    assert list(resultado.columns) == ["Longitud", "Latitud", "id", "2020_011", "2020_012", "2020_013"]


def test_borrar_columnas_sin_columnas_de_promedio():
    df = pd.DataFrame(columns=["Longitud", "Latitud", "id", "2020_011", "2020_012", "2020_013"])
    resultado = borrar_columnas(df)
    assert list(resultado.columns) == list(df.columns)


def test_invertir_columnas():
    df = pd.DataFrame({
        "id": [1],
        "Longitud": [-56.0],
        "Latitud": [-34.0],
        "2020_011": [1.5],
        "2020_012": [2.5],
        "2020_010": [2.0],
    })

    resultado = invertir_columnas(df)

    assert list(resultado.columns) == ["longitud", "latitud", "valor", "fecha_inicio", "fecha_fin"]
    assert len(resultado) == 2

    fila_periodo_1 = resultado.iloc[0]
    assert fila_periodo_1["longitud"] == -56.0
    assert fila_periodo_1["latitud"] == -34.0
    assert fila_periodo_1["valor"] == 1.5
    assert fila_periodo_1["fecha_inicio"] == pd.Timestamp(2020, 1, 1, 0, 0, 0)
    assert fila_periodo_1["fecha_fin"] == pd.Timestamp(2020, 1, 10, 23, 59, 59)

    fila_periodo_2 = resultado.iloc[1]
    assert fila_periodo_2["valor"] == 2.5
    assert fila_periodo_2["fecha_inicio"] == pd.Timestamp(2020, 1, 11, 0, 0, 0)
    assert fila_periodo_2["fecha_fin"] == pd.Timestamp(2020, 1, 20, 23, 59, 59)
