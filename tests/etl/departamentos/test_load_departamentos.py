import pytest

from etl.departamentos.load_departamentos import _fix_geometry


def test_fix_geometry_polygon_se_devuelve_sin_cambios():
    geometry = {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}

    assert _fix_geometry(geometry) is geometry


def test_fix_geometry_multipolygon_se_devuelve_sin_cambios():
    geometry = {
        "type": "MultiPolygon",
        "coordinates": [[[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]],
    }

    assert _fix_geometry(geometry) is geometry


def test_fix_geometry_linestring_cerrado_se_convierte_a_polygon():
    geometry = {
        "type": "LineString",
        "coordinates": [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]],
    }

    resultado = _fix_geometry(geometry)

    assert resultado["type"] == "Polygon"


def test_fix_geometry_linestring_abierto_usa_convex_hull():
    geometry = {
        "type": "LineString",
        "coordinates": [[0, 0], [1, 0], [1, 1]],
    }

    resultado = _fix_geometry(geometry)

    assert resultado["type"] == "Polygon"


def test_fix_geometry_punto_lanza_value_error():
    geometry = {"type": "Point", "coordinates": [0, 0]}

    with pytest.raises(ValueError):
        _fix_geometry(geometry)
