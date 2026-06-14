import pandas as pd

from etl.gems.pre_processing import pre_process_gems_params


def _base_df(**overrides):
    data = {
        "Sample Date": ["2020-01-15"],
        "Sample Time": ["10:30:00"],
        "Parameter Code": [" TOTCOLI "],
        "Value": ["12.5"],
        "Unit": ["mg/l"],
        "Data Quality": [" Good "],
        "Depth": ["1.0"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_pre_process_gems_params_fecha_con_hora():
    resultado = pre_process_gems_params(_base_df())

    fila = resultado.iloc[0]
    assert fila["fecha_inicio"] == pd.Timestamp("2020-01-15 10:30:00")
    assert fila["fecha_fin"] == pd.Timestamp("2020-01-16 10:30:00")
    assert fila["granularidad"] == "DIA"
    assert fila["value_cat"] is None


def test_pre_process_gems_params_fallback_sin_hora():
    resultado = pre_process_gems_params(_base_df(**{"Sample Time": [None]}))

    fila = resultado.iloc[0]
    assert fila["fecha_inicio"] == pd.Timestamp("2020-01-15")
    assert fila["fecha_fin"] == pd.Timestamp("2020-01-16")


def test_pre_process_gems_params_renombra_y_limpia_columnas():
    resultado = pre_process_gems_params(_base_df())

    fila = resultado.iloc[0]
    assert fila["code"] == "TOTCOLI"
    assert fila["unit"] == "mg/l"
    assert fila["data_quality"] == "Good"
    assert fila["value"] == 12.5
    assert fila["depth"] == 1.0


def test_pre_process_gems_params_unidad_ph_dimensionless():
    resultado = pre_process_gems_params(_base_df(**{"Parameter Code": ["pH"], "Unit": ["---"]}))

    assert resultado.iloc[0]["unit"] == "dimensionless"


def test_pre_process_gems_params_descarta_value_no_numerico():
    resultado = pre_process_gems_params(_base_df(**{"Value": ["no_numerico"]}))

    assert len(resultado) == 0


def test_pre_process_gems_params_elimina_columnas_innecesarias():
    df = _base_df(**{
        "Analysis Method Code": ["X"],
        "Value Flags": ["Y"],
        "Integrated Value": ["Z"],
        "Remark": ["r"],
        "License Information": ["lic"],
    })

    resultado = pre_process_gems_params(df)

    for col in ["Analysis Method Code", "Value Flags", "Integrated Value", "Remark", "License Information", "Sample Date", "Sample Time"]:
        assert col not in resultado.columns
