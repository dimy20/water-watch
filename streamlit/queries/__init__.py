from .departamentos import (
    get_departamentos_con_datos,
    get_departamentos_geojson,
    get_pct_presencia_por_departamento,
)
from .ose import get_evolucion_calidad, transformar_para_dashboard
from .gems import get_estaciones_por_departamento, get_gems_evolucion, get_gems_bacterio_por_departamento
from .grillas import get_hidrico_suelo_por_departamento, TIPOS
