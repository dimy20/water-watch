import psycopg
import os
from psycopg import Connection

from pymongo import MongoClient
from pymongo.database import Database

def get_postgres_conn() -> Connection:
    return psycopg.connect(os.environ["ETL_DATABASE_URL"])

def get_mongo_conn() -> Database:
    client = MongoClient(os.environ["ETL_MONGO_URL"], uuidRepresentation="standard")
    return client["grp05db"]

def get_streamlit_postgres_conn() -> Connection:
    return psycopg.connect(os.environ["STREAMLIT_DATABASE_URL"])

def get_streamlit_mongo_conn() -> Database:
    client = MongoClient(os.environ["STREAMLIT_MONGO_URL"], uuidRepresentation="standard")
    return client["grp05db"]
