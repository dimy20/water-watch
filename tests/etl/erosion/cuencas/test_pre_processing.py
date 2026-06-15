import pandas as pd
import pytest

from etl.erosion.cuencas.pre_processing import cambiar_nombres, fix_nombres, get_repetidos


def test_get_repetidos_sin_duplicados():
    df = pd.DataFrame({"NOMBRE": ["Cuenca A", "Cuenca B", "Cuenca C"]})

    assert get_repetidos(df) == set()


def test_get_repetidos_con_duplicados_ignora_sin_nombre():
    df = pd.DataFrame({"NOMBRE": ["Cuenca A", "Cuenca A", "SIN_NOMBRE", "SIN_NOMBRE", "Cuenca B"]})

    assert get_repetidos(df) == {"Cuenca A"}


def test_fix_nombres_asigna_sufijos_a_duplicados():
    df = pd.DataFrame({"NOMBRE": ["Cuenca A", "Cuenca A", "Cuenca B"]})

    nuevos = fix_nombres(df)

    assert nuevos == ["Cuenca A_1", "Cuenca A_2", "Cuenca B"]


def test_fix_nombres_asigna_areas_disponibles_a_nulos():
    df = pd.DataFrame({"NOMBRE": [None, None, "Cuenca B"]})

    nuevos = fix_nombres(df)

    assert nuevos == ["AREA_A", "AREA_B", "Cuenca B"]


def test_fix_nombres_sin_repetidos_ni_nulos_conserva_nombres():
    df = pd.DataFrame({"NOMBRE": ["Cuenca A", "Cuenca B"]})

    nuevos = fix_nombres(df)

    assert nuevos == ["Cuenca A", "Cuenca B"]


def test_cambiar_nombres_actualiza_columna():
    df = pd.DataFrame({"NOMBRE": ["Cuenca A", "Cuenca A"], "valor": [1, 2]})

    resultado = cambiar_nombres(df, ["Cuenca A_1", "Cuenca A_2"])

    assert list(resultado["NOMBRE"]) == ["Cuenca A_1", "Cuenca A_2"]
    assert list(df["NOMBRE"]) == ["Cuenca A", "Cuenca A"]


def test_cambiar_nombres_longitud_distinta_lanza_error():
    df = pd.DataFrame({"NOMBRE": ["Cuenca A", "Cuenca B"]})

    with pytest.raises(ValueError):
        cambiar_nombres(df, ["Cuenca A_1"])
