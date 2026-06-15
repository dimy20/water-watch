from etl.erosion.suelos.loading import crear_fila_erosion_suelo
from etl.utils import create_id


def test_crear_fila_erosion_suelo_estructura():
    area_id = create_id("geometry-placeholder")

    fila = crear_fila_erosion_suelo(area_id, "10.1", "Tacuarembo", 0.28, "Argisoles")

    erosion_id, fila_area_id, grupo_coneat, perfil_modal, factor_k, taxonomia = fila
    assert fila_area_id == area_id
    assert grupo_coneat == "10.1"
    assert perfil_modal == "Tacuarembo"
    assert factor_k == 0.28
    assert taxonomia == "Argisoles"


def test_crear_fila_erosion_suelo_id_determinista():
    area_id = create_id("geometry-placeholder")

    fila_1 = crear_fila_erosion_suelo(area_id, "10.1", "Tacuarembo", 0.28, "Argisoles")
    fila_2 = crear_fila_erosion_suelo(area_id, "10.1", "Tacuarembo", 0.28, "Argisoles")

    assert fila_1[0] == fila_2[0]


def test_crear_fila_erosion_suelo_id_cambia_con_factor_k():
    area_id = create_id("geometry-placeholder")

    fila_base = crear_fila_erosion_suelo(area_id, "10.1", "Tacuarembo", 0.28, "Argisoles")
    fila_otro_factor = crear_fila_erosion_suelo(area_id, "10.1", "Tacuarembo", 0.30, "Argisoles")

    assert fila_base[0] != fila_otro_factor[0]
