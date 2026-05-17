import psycopg
import os

DATABASE_URL = os.environ["DATABASE_URL"]

def get_db_conn():
    return psycopg.connect(DATABASE_URL)
