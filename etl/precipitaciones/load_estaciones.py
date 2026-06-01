from pathlib import Path

from pymongo import UpdateOne

from db import get_mongo_conn
from etl.utils import crear_estacion_doc
from etl.precipitaciones.logger import log

DATA_DIR = Path("./data/precipitaciones")

ESTACIONES = {
    "La Estanzuela": DATA_DIR / "La Estanzuela",
    "Las Brujas": DATA_DIR / "Las Brujas",
    "SaltoGrande": DATA_DIR / "SaltoGrande",
    "Tacuarembo": DATA_DIR / "Tacuarembo",
    "Treinta y Tres": DATA_DIR / "Treinta y Tres",
}


def _leer_coords(estacion_dir: Path) -> tuple[float, float]:
    text = (estacion_dir / "coords.txt").read_text().strip()
    lon, lat = [float(x.strip()) for x in text.split(",")]
    return lat, lon


def load():
    mongo = get_mongo_conn()
    ops = []
    for nombre, estacion_dir in ESTACIONES.items():
        lat, lon = _leer_coords(estacion_dir)
        doc = crear_estacion_doc(nombre, lat, lon)
        ops.append(UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True))

    result = mongo["estaciones"].bulk_write(ops, ordered=False)
    log.info(f"MongoDB: {result.upserted_count} estaciones insertadas, {result.matched_count} ya existían")
