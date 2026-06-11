
import re
from pathlib import Path
from typing import Callable

ResourceResolver = Callable[[dict], Path | None]

# Los datos hasta este año (exclusive) ya fueron cargados en la carga inicial
# (data/, 2015-2025). El CDC por hash solo nos interesa para archivos de
# MIN_YEAR en adelante, que son los que todavia se siguen actualizando.
MIN_YEAR = 2026


def _extract_year(filename: str) -> int | None:
    match = re.search(r"(20\d{2})", filename)
    return int(match.group(1)) if match else None


def _resolver_inumet(resource: dict) -> Path | None:
    if resource.get("format", "").upper() != "CSV":
        return None
    name = resource.get("name", "").lower()
    if "precipitaci" in name:
        return Path("inumet_precipitacion_acumulada_horaria.csv")
    if "humedad" in name:
        return Path("inumet_humedad_relativa.csv")
    return None


def _resolver_grillas(tipo: str) -> ResourceResolver:
    prefijo = f"inia_gras_{tipo.lower()}"

    def resolver(resource: dict) -> Path | None:
        if resource.get("format", "").upper() != "CSV":
            return None
        url_filename = resource["url"].rsplit("/", 1)[-1]
        if not url_filename.lower().startswith(prefijo):
            return None
        anio = _extract_year(url_filename)
        if anio is None or anio < MIN_YEAR:
            return None
        return Path("grillas") / tipo.lower() / url_filename

    return resolver


def _resolver_precipitaciones(estacion_dir: str, sufijo: str) -> ResourceResolver:
    prefijo = f"ppt_tmax_tmin_{sufijo}"

    def resolver(resource: dict) -> Path | None:
        if resource.get("format", "").upper() != "CSV":
            return None
        url_filename = resource["url"].rsplit("/", 1)[-1]
        if not url_filename.lower().startswith(prefijo):
            return None
        anio = _extract_year(url_filename)
        if anio is None or anio < MIN_YEAR:
            return None
        return Path("precipitaciones") / estacion_dir / url_filename

    return resolver


def _resolver_reclamos(resource: dict) -> Path | None:
    if resource.get("format", "").upper() != "CSV":
        return None
    url_filename = resource["url"].rsplit("/", 1)[-1]
    if not url_filename.startswith("solicitudes_y_reclamos-comerciales_"):
        return None
    anio = _extract_year(url_filename)
    if anio is None or anio < MIN_YEAR:
        return None
    return Path("reclamos") / url_filename


def _resolver_calidad_agua(resource: dict) -> Path | None:
    name = resource.get("name", "").lower()
    if "bacteriolog" in name and resource.get("format", "").upper() == "CSV":
        return Path("calidad_de_agua_bacteriologia.csv")
    return None


SOURCES: dict[str, tuple[str, ResourceResolver]] = {
    "inia-anr-por-grilla": ("grillas", _resolver_grillas("ANR")),
    "inia-pad-por-grilla": ("grillas", _resolver_grillas("PAD")),
    "inia-ibh-por-grilla": ("grillas", _resolver_grillas("IBH")),

    "inia-precipitacion-temps-extremas-lb": ("precipitaciones.load_registros", _resolver_precipitaciones("Las Brujas", "lb")),
    "inia-precipitacion-temps-extremas-tyt": ("precipitaciones.load_registros", _resolver_precipitaciones("Treinta y Tres", "tyt")),
    "inia-precipitacion-temps-extremas-sg": ("precipitaciones.load_registros", _resolver_precipitaciones("SaltoGrande", "sg")),
    "inia-precipitacion-temps-extremas-tb": ("precipitaciones.load_registros", _resolver_precipitaciones("Tacuarembo", "tb")),
    "inia-precipitacion-temps-extremas-le": ("precipitaciones.load_registros", _resolver_precipitaciones("La Estanzuela", "le")),

    "reclamos-comerciales": ("reclamos", _resolver_reclamos),
    "calidad-de-agua": ("bacteriologia_ose", _resolver_calidad_agua),

    "inumet-observaciones-meteorologicas-precipitacion-puntual-en-el-uruguay": ("inumet", _resolver_inumet),
    "inumet-observaciones-meteorologicas-humedad-relativa-en-el-uruguay": ("inumet", _resolver_inumet),
}
