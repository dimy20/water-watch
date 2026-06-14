from shapely.geometry import Point

from etl.areas import crear_area_doc
from etl.utils import create_id


def test_crear_area_doc_estructura():
    geometry = Point(1, 2)

    doc = crear_area_doc(geometry, "Area A")

    assert doc["_id"] == create_id(geometry, "Area A")
    assert doc["nombre"] == "Area A"
    assert doc["geometry"] == {"type": "Point", "coordinates": (1.0, 2.0)}


def test_crear_area_doc_sin_nombre_usa_sin_nombre():
    geometry = Point(1, 2)

    doc = crear_area_doc(geometry)

    assert doc["nombre"] == "SIN_NOMBRE"
    assert doc["_id"] == create_id(geometry, None)


def test_crear_area_doc_id_determinista():
    geometry = Point(1, 2)

    doc_1 = crear_area_doc(geometry, "Area A")
    doc_2 = crear_area_doc(geometry, "Area A")

    assert doc_1["_id"] == doc_2["_id"]
