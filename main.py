# psycog
import init_logger
from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path=".env.local")
import hashlib
from etl.cuencas.loading import load as load_cuencas

#entry point
def main():
    load_cuencas()

if __name__ == "__main__": # workaround 
    main()
