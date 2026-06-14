import pytest

from scripts.clean_etl_data import (
    MONGO_COLLECTION_BY_ETL_ID,
    PG_TABLE_BY_ETL_ID,
    cleaning_plan,
    topo_sort,
    unique_in_order,
)


def test_topo_sort_respeta_dependencias():
    graph = [
        {"id": "a", "requires": []},
        {"id": "b", "requires": ["a"]},
        {"id": "c", "requires": ["b"]},
    ]

    orden = topo_sort(graph)

    assert orden.index("a") < orden.index("b") < orden.index("c")


def test_topo_sort_nodos_sin_dependencias_van_primero_y_ordenados():
    graph = [
        {"id": "b", "requires": []},
        {"id": "a", "requires": []},
    ]

    assert topo_sort(graph) == ["a", "b"]


def test_topo_sort_dependencia_circular_lanza_error():
    graph = [
        {"id": "a", "requires": ["b"]},
        {"id": "b", "requires": ["a"]},
    ]

    with pytest.raises(RuntimeError):
        topo_sort(graph)


def test_unique_in_order_elimina_duplicados_preservando_orden():
    assert unique_in_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_unique_in_order_lista_vacia():
    assert unique_in_order([]) == []


def test_cleaning_plan_incluye_todas_las_tablas_y_colecciones_conocidas():
    pg_tables, mongo_collections = cleaning_plan()

    assert set(pg_tables) == set(PG_TABLE_BY_ETL_ID.values())
    assert set(mongo_collections) == set(MONGO_COLLECTION_BY_ETL_ID.values())


def test_cleaning_plan_sin_duplicados():
    pg_tables, mongo_collections = cleaning_plan()

    assert len(pg_tables) == len(set(pg_tables))
    assert len(mongo_collections) == len(set(mongo_collections))
