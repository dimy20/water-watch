from pathlib import Path

from etl.ckan_sources import (
    MIN_YEAR,
    _extract_year,
    _resolver_calidad_agua,
    _resolver_grillas,
    _resolver_inumet,
    _resolver_precipitaciones,
    _resolver_reclamos,
)


def test_extract_year_encuentra_anio():
    assert _extract_year("inia_gras_anr_2026_03.csv") == 2026


def test_extract_year_sin_anio_retorna_none():
    assert _extract_year("archivo_sin_fecha.csv") is None


def test_resolver_inumet_precipitacion():
    resource = {"format": "CSV", "name": "Precipitación acumulada horaria"}

    assert _resolver_inumet(resource) == Path("inumet_precipitacion_acumulada_horaria.csv")


def test_resolver_inumet_humedad():
    resource = {"format": "CSV", "name": "Humedad relativa"}

    assert _resolver_inumet(resource) == Path("inumet_humedad_relativa.csv")


def test_resolver_inumet_formato_no_csv_retorna_none():
    resource = {"format": "XLSX", "name": "Precipitación acumulada horaria"}

    assert _resolver_inumet(resource) is None


def test_resolver_inumet_nombre_no_reconocido_retorna_none():
    resource = {"format": "CSV", "name": "Otro dataset"}

    assert _resolver_inumet(resource) is None


def test_resolver_grillas_archivo_valido():
    resolver = _resolver_grillas("ANR")
    resource = {"format": "CSV", "url": f"https://example.com/inia_gras_anr_{MIN_YEAR}_03.csv"}

    assert resolver(resource) == Path("grillas") / "anr" / f"inia_gras_anr_{MIN_YEAR}_03.csv"


def test_resolver_grillas_prefijo_incorrecto_retorna_none():
    resolver = _resolver_grillas("ANR")
    resource = {"format": "CSV", "url": f"https://example.com/inia_gras_pad_{MIN_YEAR}_03.csv"}

    assert resolver(resource) is None


def test_resolver_grillas_anio_anterior_a_min_year_retorna_none():
    resolver = _resolver_grillas("ANR")
    resource = {"format": "CSV", "url": f"https://example.com/inia_gras_anr_{MIN_YEAR - 1}_03.csv"}

    assert resolver(resource) is None


def test_resolver_grillas_formato_no_csv_retorna_none():
    resolver = _resolver_grillas("ANR")
    resource = {"format": "XLSX", "url": f"https://example.com/inia_gras_anr_{MIN_YEAR}_03.csv"}

    assert resolver(resource) is None


def test_resolver_precipitaciones_archivo_valido():
    resolver = _resolver_precipitaciones("Las Brujas", "lb")
    resource = {"format": "CSV", "url": f"https://example.com/ppt_tmax_tmin_lb_{MIN_YEAR}.csv"}

    assert resolver(resource) == Path("precipitaciones") / "Las Brujas" / f"ppt_tmax_tmin_lb_{MIN_YEAR}.csv"


def test_resolver_precipitaciones_prefijo_incorrecto_retorna_none():
    resolver = _resolver_precipitaciones("Las Brujas", "lb")
    resource = {"format": "CSV", "url": f"https://example.com/ppt_tmax_tmin_tyt_{MIN_YEAR}.csv"}

    assert resolver(resource) is None


def test_resolver_reclamos_archivo_valido():
    resource = {"format": "CSV", "url": f"https://example.com/solicitudes_y_reclamos-comerciales_{MIN_YEAR}.csv"}

    assert _resolver_reclamos(resource) == Path("reclamos") / f"solicitudes_y_reclamos-comerciales_{MIN_YEAR}.csv"


def test_resolver_reclamos_anio_anterior_a_min_year_retorna_none():
    resource = {"format": "CSV", "url": f"https://example.com/solicitudes_y_reclamos-comerciales_{MIN_YEAR - 1}.csv"}

    assert _resolver_reclamos(resource) is None


def test_resolver_reclamos_prefijo_incorrecto_retorna_none():
    resource = {"format": "CSV", "url": f"https://example.com/otro_archivo_{MIN_YEAR}.csv"}

    assert _resolver_reclamos(resource) is None


def test_resolver_calidad_agua_bacteriologia_csv():
    resource = {"format": "CSV", "name": "Calidad de agua - Bacteriología"}

    assert _resolver_calidad_agua(resource) == Path("calidad_de_agua_bacteriologia.csv")


def test_resolver_calidad_agua_sin_match_retorna_none():
    resource = {"format": "CSV", "name": "Otro dataset"}

    assert _resolver_calidad_agua(resource) is None
