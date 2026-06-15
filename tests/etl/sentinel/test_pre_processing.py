import importlib
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture
def pre_processing_module():
    """Importa etl.sentinel.pre_processing sin pegarle a la red real.

    El modulo hace `catalog = Client.open(EARTH_SEARCH_URL)` al importarse,
    lo cual dispara una llamada HTTP. Se mockea `Client.open` antes de
    importar (forzando una recarga) para evitar esa llamada en los tests.
    """
    with patch("pystac_client.Client.open", return_value=MagicMock()):
        sys.modules.pop("etl.sentinel.pre_processing", None)
        module = importlib.import_module("etl.sentinel.pre_processing")
        yield module
    sys.modules.pop("etl.sentinel.pre_processing", None)


def test_compute_index_series_sin_items_retorna_lista_vacia(pre_processing_module, monkeypatch):
    mod = pre_processing_module

    mock_catalog = MagicMock()
    mock_catalog.search.return_value.item_collection.return_value = []
    monkeypatch.setattr(mod, "catalog", mock_catalog)

    resultado = mod.compute_index_series([-34.9, -56.2], 0.01, 10, "NDCI")

    assert resultado == []


def test_compute_index_series_filtra_nan_y_convierte_valores(pre_processing_module, monkeypatch):
    mod = pre_processing_module

    mock_catalog = MagicMock()
    mock_catalog.search.return_value.item_collection.return_value = ["item1"]
    monkeypatch.setattr(mod, "catalog", mock_catalog)

    serie = SimpleNamespace(
        time=SimpleNamespace(values=np.array([
            np.datetime64("2023-01-01"),
            np.datetime64("2023-01-09"),
        ])),
        values=np.array([0.5, np.nan]),
    )

    fake_indice = MagicMock()
    fake_indice.median.return_value.compute.return_value = serie
    monkeypatch.setitem(mod.INDICES["NDCI"], "formula", lambda bands: fake_indice)

    mock_stack = MagicMock()
    mock_stack.where.return_value = mock_stack
    mock_stack.sel.return_value = mock_stack
    monkeypatch.setattr(mod.stackstac, "stack", MagicMock(return_value=mock_stack))

    resultado = mod.compute_index_series([-34.9, -56.2], 0.01, 10, "NDCI")

    assert resultado == [(date(2023, 1, 1), 0.5)]
