import uuid

from etl.utils import create_id, crear_estacion_doc


def test_create_id_es_determinista():
    assert create_id("Rivera", -30.9, -55.5) == create_id("Rivera", -30.9, -55.5)


def test_create_id_distintos_valores_distinto_id():
    assert create_id("Rivera", -30.9, -55.5) != create_id("Salto", -31.4, -57.9)


def test_create_id_orden_de_argumentos_importa():
    assert create_id("a", "b") != create_id("b", "a")


def test_create_id_join_no_colisiona_por_concatenacion():
    assert create_id("a", "b") != create_id("ab")


def test_create_id_retorna_uuid():
    assert isinstance(create_id("Rivera", -30.9, -55.5), uuid.UUID)


def test_create_id_soporta_distintos_tipos_de_argumentos():
    resultado = create_id("Rivera", -30.9, -55.5, 1, None)
    assert isinstance(resultado, uuid.UUID)
    assert resultado == create_id("Rivera", -30.9, -55.5, 1, None)


def test_crear_estacion_doc_id_coincide_con_create_id():
    doc = crear_estacion_doc("Rivera", -30.9, -55.5)
    assert doc["_id"] == create_id("Rivera", -30.9, -55.5)


def test_crear_estacion_doc_estructura():
    doc = crear_estacion_doc("Rivera", -30.9, -55.5)
    assert doc["nombre"] == "Rivera"
    assert doc["location"]["type"] == "Point"
    assert doc["location"]["coordinates"] == [-55.5, -30.9]


def test_crear_estacion_doc_es_idempotente():
    doc_1 = crear_estacion_doc("Rivera", -30.9, -55.5)
    doc_2 = crear_estacion_doc("Rivera", -30.9, -55.5)
    assert doc_1["_id"] == doc_2["_id"]
