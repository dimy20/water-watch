from etl.precipitaciones.load_estaciones import _leer_coords


def test_leer_coords_orden_lon_lat(tmp_path):
    (tmp_path / "coords.txt").write_text("-57.9, -34.3")

    lat, lon = _leer_coords(tmp_path)

    assert lat == -34.3
    assert lon == -57.9


def test_leer_coords_con_espacios_y_salto_de_linea(tmp_path):
    (tmp_path / "coords.txt").write_text("  -56.0 ,  -33.5  \n")

    lat, lon = _leer_coords(tmp_path)

    assert lat == -33.5
    assert lon == -56.0
