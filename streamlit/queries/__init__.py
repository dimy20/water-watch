from .departamentos import (
    get_departamentos_con_datos,
    get_departamentos_geojson,
    get_pct_presencia_por_departamento,
)
from .ose import (
    get_evolucion_calidad,
    transformar_para_dashboard,
    get_patron_estacional,
    get_pct_presencia_por_departamento_periodo,
)
from .gems import get_estaciones_por_departamento, get_gems_evolucion, get_gems_bacterio_por_departamento
from .grillas import get_hidrico_suelo_por_departamento, TIPOS
from .riesgo import get_riesgo_por_departamento
from .reclamos import (
    get_reclamos_por_departamento,
    get_reclamos_trimestral,
    get_correlacion_reclamos_calidad,
)
from .precipitacion_ndci import (
    get_locations_con_ndci,
    get_precipitacion_vs_ndci,
    get_correlacion_por_lag,
    get_punto_grilla_cercano_sentinel,
    get_punto_grilla_coords,
)
