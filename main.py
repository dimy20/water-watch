# psycog
#import init_logger
from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path=".env.local")
import hashlib

from etl.erosion.cuencas.loading import load as load_erosion_cuenca
from etl.erosion.suelos.loading import load as load_erosion_suelos
from etl.inumet.loading import load as load_inumet
from etl.estaciones.loading import load as load_estaciones
from etl.grillas.loading import load as load_grillas

#entry point
def main():
    #load_grillas("IBH")
    #load_grillas("PAD")
    #load_grillas("ANR")
    pass

if __name__ == "__main__": # workaround 
    main()
