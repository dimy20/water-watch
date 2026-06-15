import pandas as pd

from etl.erosion.suelos.pre_processing import pre_process


def test_pre_process_descarta_factor_k_nulo():
    df = pd.DataFrame({
        "Factor_K": [0.2, None, 0.35],
        "Taxonomia_": ["A", "B", "C"],
    })

    resultado = pre_process(df)

    assert len(resultado) == 2
    assert list(resultado["Taxonomia_"]) == ["A", "C"]


def test_pre_process_sin_nulos_conserva_todas_las_filas():
    df = pd.DataFrame({
        "Factor_K": [0.2, 0.35],
        "Taxonomia_": ["A", "C"],
    })

    resultado = pre_process(df)

    assert len(resultado) == 2
