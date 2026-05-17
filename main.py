# psycog
from dotenv import load_dotenv
load_dotenv(override=True)
from db import get_db_conn
import os

if __name__ == "__main__":
    print(os.environ["DATABASE_URL"])
    
