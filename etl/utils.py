import uuid
import hashlib

def create_id(*args) -> uuid.UUID:
    payload = "|".join(str(a) for a in args).encode("utf-8")
	#md5 -> 128 bits compatible con UUID
    return uuid.UUID(bytes=hashlib.md5(payload).digest())


def crear_estacion_doc(nombre: str, latitud: float, longitud: float) -> dict:
    location_id = create_id(nombre, latitud, longitud)
    return {
        "_id": location_id,
        "nombre": nombre,
        "location": {
            "type": "Point",
            "coordinates": [longitud, latitud],
        },
    }


# SE USA ASI:
	#create_id(nombre, area, descrpition, hijos, money, gatos, perros, ranas)