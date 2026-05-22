from shapely.geometry import mapping
from etl.utils import create_id

def crear_area_doc(geometry, nombre: str = None):
	area_id = create_id(geometry, nombre)
	if not nombre:
		nombre = "SIN_NOMBRE"
	area_doc = {
		"_id" : area_id,
		"nombre": nombre,
		"geometry": mapping(geometry)
	}
	return area_doc