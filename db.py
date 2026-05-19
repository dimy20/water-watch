import psycopg # Libreria de python para establecer una conexio directa con PostgreSQL.
import os
from psycopg import Connection

from pymongo import MongoClient
from pymongo.database import Database

DATABASE_URL = os.environ["DATABASE_URL"]
MONGO_URL = os.environ["MONGO_URL"]

def get_postgres_conn() -> Connection:
    return psycopg.connect(DATABASE_URL)

def get_mongo_conn() -> Database:
    client = MongoClient(MONGO_URL)
    return client["grp05db"]