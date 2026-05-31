import json

from pymongo import UpdateOne
from shapely.geometry import shape, mapping
from shapely.ops import polygonize, snap, unary_union

from db import get_mongo_conn
from etl.utils import create_id
from etl.departamentos.logger import log

DATA_FILE = "./data/departamentos.geojson"

TIPOS_VALIDOS = {"Polygon", "MultiPolygon"}


def _fix_geometry(geometry: dict) -> dict:
    if geometry["type"] in TIPOS_VALIDOS:
        return geometry

    geom = shape(geometry)

    polygons = list(polygonize(geom))

    for tolerance in (0.0001, 0.001, 0.01):
        if polygons:
            break
        snapped = snap(geom, geom, tolerance=tolerance)
        polygons = list(polygonize(snapped))

    if not polygons:
        # Ultimo recurso: convex hull del contorno
        hull = geom.convex_hull
        if hull.geom_type in TIPOS_VALIDOS:
            log.warning(f"Usando convex_hull como fallback para geometria tipo {geometry['type']}")
            return mapping(hull)
        raise ValueError(f"No se pudo convertir geometria tipo {geometry['type']} a poligono")

    fixed = polygons[0] if len(polygons) == 1 else unary_union(polygons)
    return mapping(fixed)


def load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        log.error(f"Archivo no encontrado: {DATA_FILE}")
        return
    except Exception as e:
        log.error(f"Error leyendo {DATA_FILE}: {e}")
        return

    features = data.get("features", [])
    log.info(f"Cargando {len(features)} departamentos")

    ops = []
    for feature in features:
        props = feature["properties"]
        nombre = props["admlnm"]
        codigo = props["admlcd"]

        try:
            geometry = _fix_geometry(feature["geometry"])
        except ValueError as e:
            log.error(f"Departamento '{nombre}' omitido: {e}")
            continue

        doc_id = create_id(nombre, codigo)
        doc = {
            "_id": doc_id,
            "nombre": nombre,
            "codigo": codigo,
            "geometry": geometry,
        }
        ops.append(UpdateOne({"_id": doc_id}, {"$set": doc}, upsert=True))

    if not ops:
        log.warning("No hay operaciones para ejecutar")
        return

    try:
        mongo = get_mongo_conn()
        result = mongo["departamentos"].bulk_write(ops, ordered=False)
        log.info(f"MongoDB: {result.upserted_count} insertados, {result.matched_count} actualizados")
    except Exception as e:
        log.error(f"Error escribiendo en MongoDB: {e}")
