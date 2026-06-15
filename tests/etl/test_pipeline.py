import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(scope="module")
def pipeline_module():
    """Importa etl.pipeline sin pegarle a la red real.

    etl.pipeline importa (transitivamente, via etl.sentinel.load_locations
    y load_mediciones) a etl.sentinel.pre_processing, que hace
    `Client.open(...)` al importarse. Se mockea `Client.open` antes de
    importar para evitar esa llamada de red.
    """
    with patch("pystac_client.Client.open", return_value=MagicMock()):
        sys.modules.pop("etl.pipeline", None)
        sys.modules.pop("etl.sentinel.pre_processing", None)
        sys.modules.pop("etl.sentinel.load_locations", None)
        sys.modules.pop("etl.sentinel.load_mediciones", None)
        module = importlib.import_module("etl.pipeline")
        yield module


def test_load_graph_lee_el_grafo_real(pipeline_module):
    graph = pipeline_module.load_graph()

    ids = {item["id"] for item in graph}
    assert "departamentos" in ids
    assert "sentinel.load_mediciones_ndci" in ids


def test_get_required_nodes_incluye_dependencias_transitivas(pipeline_module):
    graph = pipeline_module.load_graph()

    required = pipeline_module.get_required_nodes(graph, "sentinel.load_mediciones_ndci")

    assert required == {"sentinel.load_mediciones_ndci", "sentinel.load_locations"}


def test_get_required_nodes_sin_dependencias(pipeline_module):
    graph = pipeline_module.load_graph()

    required = pipeline_module.get_required_nodes(graph, "departamentos")

    assert required == {"departamentos"}


def test_get_required_nodes_target_inexistente_lanza_error(pipeline_module):
    graph = pipeline_module.load_graph()

    with pytest.raises(RuntimeError):
        pipeline_module.get_required_nodes(graph, "no_existe")


def test_get_load_order_respeta_dependencias(pipeline_module):
    graph = pipeline_module.load_graph()

    order = pipeline_module.get_load_order(graph)

    assert order.index("departamentos") < order.index("bacteriologia_ose")
    assert order.index("precipitaciones.load_estaciones") < order.index("precipitaciones.load_registros")
    assert order.index("sentinel.load_locations") < order.index("sentinel.load_mediciones_ndci")
    assert order.index("sentinel.load_locations") < order.index("sentinel.load_mediciones_turbidez")
    assert set(order) == {item["id"] for item in graph}


def test_get_load_order_con_only_filtra_subgrafo(pipeline_module):
    graph = pipeline_module.load_graph()

    order = pipeline_module.get_load_order(graph, only="sentinel.load_mediciones_ndci")

    assert set(order) == {"sentinel.load_locations", "sentinel.load_mediciones_ndci"}
    assert order.index("sentinel.load_locations") < order.index("sentinel.load_mediciones_ndci")


def test_get_load_order_tarea_no_registrada_lanza_error(pipeline_module):
    graph = [{"id": "no_registrado", "requires": []}]

    with pytest.raises(RuntimeError):
        pipeline_module.get_load_order(graph)


def test_get_load_order_dependencia_circular_lanza_error(pipeline_module):
    graph = [
        {"id": "departamentos", "requires": ["estaciones"]},
        {"id": "estaciones", "requires": ["departamentos"]},
    ]

    with pytest.raises(RuntimeError):
        pipeline_module.get_load_order(graph)
