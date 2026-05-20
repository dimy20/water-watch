import uuid
from shapely.geometry import mapping

def crear_area_doc(geometry, nombre: str = None):
	area_id = str(uuid.uuid4())
	if not nombre:
		nombre = "SIN_NOMBRE"
	area_doc = {
		"_id" : area_id,
		"nombre": nombre,
		"geometry": mapping(geometry)
	}
	return area_doc