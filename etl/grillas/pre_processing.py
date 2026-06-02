import pandas as pd
import calendar
from etl.grillas.logger import log

#"./data/grillas/ibh/ini_gras_ibh2015"

# borramos las ultimas columnas de cada mes.
# las columnas siguen este patron:
# # yyyy_mmd
# 1 -> 1-10
# 2 -> 11 - 20
# 3 -> 21 - fin_mes 
# 4 -> la 4ta columna de cada mes es un promedio de la anterior, 
# no nos sirve mucho, ya que nos interesa saber como evoluciona el parametro a lo largo del tiempo
# por eso la sacamos
	
def borrar_columnas(df: pd.DataFrame) -> pd.DataFrame:
	columnas_de_promedios = [col for col in df.columns if str(col).endswith("0")]
	df = df.drop(columns=columnas_de_promedios)
	return df

#def borrar_columnas(df: pd.DataFrame) -> pd.DataFrame:
#	columnas_de_promedios = []
#
#	for i in range(5, 50, 4):
#		columna = df.columns[i]
#		columnas_de_promedios.append(columna)
#
#	df = df.drop(columns = columnas_de_promedios)
#	return df

def parse_date_column(column: str):
	parts = column.split("_")
	year = int(parts[0])
	mes = int(parts[1][:2])
	periodo = int(parts[1][-1])
	
	if periodo == 1:
		fecha_inicio = pd.Timestamp(year=year, month=mes, day=1, hour=0, minute=0, second=0)
		fecha_fin = pd.Timestamp(year=year, month=mes, day=10, hour=23, minute=59, second=59)
		return fecha_inicio, fecha_fin
	elif periodo == 2:
		fecha_inicio = pd.Timestamp(year=year, month=mes, day=11, hour=0, minute=0, second=0)
		fecha_fin = pd.Timestamp(year=year, month=mes, day=20, hour=23, minute=59, second=59)
		return fecha_inicio, fecha_fin
	elif periodo == 3:
		ultimo_dia = calendar.monthrange(year, mes)[1]
		fecha_inicio = pd.Timestamp(year=year, month=mes, day=21, hour=0, minute=0, second=0)
		fecha_fin = pd.Timestamp(year=year, month=mes, day=ultimo_dia, hour=23, minute=59, second=59)
		return fecha_inicio, fecha_fin
	else:
		log.warning(f"Columna con periodo invalido: {column}")
		raise ValueError(f"Fecha invalida, periodo = {periodo}")

def invertir_columnas(df: pd.DataFrame) -> pd.DataFrame:
	df = borrar_columnas(df)

	longitudes = []
	latitudes = []
	valores = []
	fechas_inicio = []
	fechas_fin = []

	columnas_datos = [col for col in df.columns if col not in ("Longitud", "Latitud", "id")]

	for i in range(len(df)):
		fila = df.iloc[i]
		longitud = fila["Longitud"]
		latitud = fila["Latitud"]
		for columna in columnas_datos:
			valor = float(fila[columna])
			longitudes.append(longitud)
			latitudes.append(latitud)
			valores.append(valor)
			fecha_inicio, fecha_fin = parse_date_column(columna)
			fechas_inicio.append(fecha_inicio)
			fechas_fin.append(fecha_fin)

	datos = {
		"longitud": longitudes,
		"latitud": latitudes,
		"valor": valores,
		"fecha_inicio": fechas_inicio,
		"fecha_fin": fechas_fin
	}

	return pd.DataFrame(datos)