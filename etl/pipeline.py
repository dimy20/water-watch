import json
import logging
from collections import defaultdict, deque
from pathlib import Path
from typing import Callable

from etl.bacteriologia_ose.load_bacteriologia import load as load_bacteriologia_ose
from etl.departamentos.load_departamentos import load as load_departamentos
from etl.erosion.cuencas.loading import load as load_erosion_cuencas
from etl.erosion.suelos.loading import load as load_erosion_suelos
from etl.estaciones.loading import load as load_estaciones
from etl.gems.load_estaciones import load as load_gems_estaciones
from etl.gems.load_mediciones import load as load_gems_mediciones
from etl.grillas.loading import load as load_grillas
from etl.inumet.loading import load as load_inumet
from etl.precipitaciones.load_estaciones import load as load_precipitaciones_estaciones
from etl.precipitaciones.load_registros import load as load_precipitaciones_registros
from etl.reclamos.load_reclamos import load as load_reclamos
from etl.sentinel.load_locations import load as load_sentinel_locations
from etl.sentinel.load_mediciones import load as load_sentinel_mediciones
from etl.sentinel.params import CODE_NDCI, CODE_NDTI

log = logging.getLogger(__name__)

GRAPH_PATH = Path(__file__).with_name("etl_graph.json")

Task = Callable[[], None]


TASKS: dict[str, list[Task]] = {
    "departamentos": [load_departamentos],
    "estaciones": [load_estaciones],
    "grillas": [
        lambda: load_grillas("IBH"),
        lambda: load_grillas("PAD"),
        lambda: load_grillas("ANR"),
    ],
    "erosion.cuencas": [load_erosion_cuencas],
    "erosion.suelos": [load_erosion_suelos],
    "inumet": [
        lambda: load_inumet("precipitacion"),
        lambda: load_inumet("humedad_relativa"),
    ],
    "bacteriologia_ose": [load_bacteriologia_ose],
    "precipitaciones.load_estaciones": [load_precipitaciones_estaciones],
    "precipitaciones.load_registros": [load_precipitaciones_registros],
    "gems.load_estaciones": [load_gems_estaciones],
    "gems.load_mediciones": [
        lambda: load_gems_mediciones("in_situ"),
        lambda: load_gems_mediciones("remote_sensing"),
    ],
    "reclamos": [load_reclamos],
    "sentinel.load_locations": [load_sentinel_locations],
    "sentinel.load_mediciones_ndci": [lambda: load_sentinel_mediciones(CODE_NDCI)],
    "sentinel.load_mediciones_turbidez": [lambda: load_sentinel_mediciones(CODE_NDTI)],
}


def load_graph(path: Path = GRAPH_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_required_nodes(graph: list[dict], target: str) -> set[str]:
    nodes_by_id = {item["id"]: item for item in graph}
    if target not in nodes_by_id:
        raise RuntimeError(
            f"No existe el módulo '{target}'. Opciones válidas: {', '.join(sorted(TASKS.keys()))}"
        )

    required: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in required:
            return
        required.add(node_id)
        for dependency in nodes_by_id[node_id].get("requires", []):
            visit(dependency)

    visit(target)
    return required


def get_load_order(graph: list[dict], only: str | None = None) -> list[str]:
    if only is not None:
        required = get_required_nodes(graph, only)
        graph = [item for item in graph if item["id"] in required]

    nodes = [item["id"] for item in graph]
    node_set = set(nodes)

    unknown_tasks = sorted(node_set - TASKS.keys())
    if unknown_tasks:
        raise RuntimeError(f"No hay loader registrado para: {', '.join(unknown_tasks)}")

    dependency_count = {node: 0 for node in nodes}
    dependents_by_node: dict[str, list[str]] = defaultdict(list)

    for item in graph:
        node = item["id"]
        for dependency in item.get("requires", []):
            if dependency not in node_set:
                raise RuntimeError(f"{node} depende de un nodo inexistente: {dependency}")
            dependency_count[node] += 1
            dependents_by_node[dependency].append(node)

    ready = deque(node for node in nodes if dependency_count[node] == 0)
    order = []

    while ready:
        node = ready.popleft()
        order.append(node)

        for dependent in dependents_by_node[node]:
            dependency_count[dependent] -= 1
            if dependency_count[dependent] == 0:
                ready.append(dependent)

    if len(order) != len(nodes):
        cyclic_nodes = [node for node, count in dependency_count.items() if count > 0]
        raise RuntimeError(f"Hay dependencias circulares en: {', '.join(cyclic_nodes)}")

    return order


def run_pipeline(only: str | None = None) -> None:
    graph = load_graph()
    order = get_load_order(graph, only=only)

    log.info("Orden de carga ETL: %s", " -> ".join(order))
    for node in order:
        log.info("Iniciando ETL: %s", node)
        for task in TASKS[node]:
            task()
        log.info("Finalizado ETL: %s", node)

