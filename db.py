import os
from pathlib import Path
from urllib.parse import quote_plus
from psycopg import Connection
from pymongo.database import Database
import psycopg
from pymongo import MongoClient
from bson.codec_options import CodecOptions
from bson.binary import UuidRepresentation


# ---------------------------------------------------------
# Conexiones para el ETL (credenciales separadas de Streamlit)
# ---------------------------------------------------------
def get_postgres_conn() -> Connection:
    return psycopg.connect(os.environ["ETL_DATABASE_URL"])


def get_mongo_conn() -> Database:
    client = MongoClient(os.environ["ETL_MONGO_URL"], uuidRepresentation="standard")
    return client["grp05db"]


# ---------------------------------------------------------
# Carga opcional de .env.local para entorno local
# ---------------------------------------------------------
try:
    from dotenv import load_dotenv

    env_local = Path(__file__).resolve().parent.parent / ".env.local"

    if env_local.exists():
        load_dotenv(dotenv_path=env_local, override=True)

except ImportError:
    # En Docker no es obligatorio python-dotenv,
    # porque docker compose ya inyecta las variables.
    pass


# ---------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------
def get_streamlit_postgres_conn():
    """
    Devuelve una conexión a PostgreSQL.

    Funciona en dos escenarios:

    1. Entorno local:
       usa STREAMLIT_DATABASE_URL si está definida.

       Ejemplo:
       STREAMLIT_DATABASE_URL=postgresql://usuario:password@localhost:5432/base

    2. Entorno Docker:
       arma la URL con las variables del contenedor:

       POSTGRES_USER
       POSTGRES_PASSWORD
       POSTGRES_DB
       POSTGRES_HOST opcional, por defecto 'postgres'
       POSTGRES_PORT opcional, por defecto '5432'
    """

    database_url = os.getenv("STREAMLIT_DATABASE_URL")

    if database_url:
        return psycopg.connect(database_url)

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_INTERNAL_PORT", "5432")

    if not all([user, password, db]):
        raise RuntimeError(
            "Faltan variables de conexión PostgreSQL. "
            "Definir STREAMLIT_DATABASE_URL o POSTGRES_USER, "
            "POSTGRES_PASSWORD y POSTGRES_DB."
        )

    user = quote_plus(user)
    password = quote_plus(password)

    database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

    return psycopg.connect(database_url)


# ---------------------------------------------------------
# MongoDB
# ---------------------------------------------------------
def get_streamlit_mongo_conn():
    """
    Devuelve un cliente MongoDB.

    Funciona en dos escenarios:

    1. Entorno local:
       usa STREAMLIT_MONGO_URL o MONGO_URI si está definida.

       Ejemplo:
       STREAMLIT_MONGO_URL=mongodb://usuario:password@localhost:27017/base?authSource=base

    2. Entorno Docker:
       arma la URL con las variables del contenedor:

       MONGO_APP_USER
       MONGO_APP_PASSWORD
       MONGO_APP_DB
       MONGO_HOST opcional, por defecto 'mongo'
       MONGO_PORT opcional, por defecto '27017'
    """

    mongo_url = os.getenv("STREAMLIT_MONGO_URL") or os.getenv("MONGO_URI")

    if mongo_url:
        client = MongoClient(mongo_url, uuidRepresentation="standard")
        return client["grp05db"]

    user = os.getenv("MONGO_APP_USER")
    password = os.getenv("MONGO_APP_PASSWORD")
    db = os.getenv("MONGO_APP_DB")
    host = os.getenv("MONGO_HOST", "mongo")
    port = os.getenv("MONGO_INTERNAL_PORT", "27017")

    if not all([user, password, db]):
        raise RuntimeError(
            "Faltan variables de conexión MongoDB. "
            "Definir STREAMLIT_MONGO_URL o MONGO_APP_USER, "
            "MONGO_APP_PASSWORD y MONGO_APP_DB."
        )

    user = quote_plus(user)
    password = quote_plus(password)

    mongo_url = (
        f"mongodb://{user}:{password}@{host}:{port}/{db}"
        f"?authSource={db}"
    )
    client = MongoClient(mongo_url, uuidRepresentation="standard")
    return client["grp05db"]