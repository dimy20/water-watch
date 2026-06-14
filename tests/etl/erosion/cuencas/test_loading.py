from etl.erosion.cuencas.loading import crear_fila_erosion_cuenca
from etl.utils import create_id


def test_crear_fila_erosion_cuenca_estructura():
    area_id = create_id("Cuenca A", "geometry-placeholder")

    fila = crear_fila_erosion_cuenca(area_id, 0.42, 2)

    erosion_id, fila_area_id, ponderacion, cluster = fila
    assert fila_area_id == area_id
    assert ponderacion == 0.42
    assert cluster == 2


def test_crear_fila_erosion_cuenca_id_determinista():
    area_id = create_id("Cuenca A", "geometry-placeholder")

    fila_1 = crear_fila_erosion_cuenca(area_id, 0.42, 2)
    fila_2 = crear_fila_erosion_cuenca(area_id, 0.42, 2)

    assert fila_1[0] == fila_2[0]


def test_crear_fila_erosion_cuenca_id_cambia_con_ponderacion_o_cluster():
    area_id = create_id("Cuenca A", "geometry-placeholder")

    fila_base = crear_fila_erosion_cuenca(area_id, 0.42, 2)
    fila_otra_ponderacion = crear_fila_erosion_cuenca(area_id, 0.50, 2)
    fila_otro_cluster = crear_fila_erosion_cuenca(area_id, 0.42, 3)

    assert fila_base[0] != fila_otra_ponderacion[0]
    assert fila_base[0] != fila_otro_cluster[0]
