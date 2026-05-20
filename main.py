# psycog
import init_logger
from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path=".env.local")
import hashlib

from etl.erosion.cuencas.loading import load as load_erosion_cuenca
from etl.erosion.suelos.loading import load as load_erosion_suelos

#entry point
def main():
    #load_erosion_cuenca()
    load_erosion_suelos()

if __name__ == "__main__": # workaround 
    main()
