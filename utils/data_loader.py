"""
Carga y unión de las bases de datos del proyecto.

Fuentes:
- data/historico_avisos_proc.xlsx  -> incidentes (avisos) sobre torres de energía
- data/equipos_proc.xlsx           -> catálogo de equipos/torres (ubicación, departamento, CTE)

Se cachea en memoria con lru_cache para no releer los Excel en cada callback
(ver notebook V06: "Uso de cache para datos grandes"). Como los archivos son
pequeños (<400 KB) no se requiere Flask-Caching en disco; si el volumen de
datos crece, esa es la siguiente mejora recomendada.
"""

from functools import lru_cache
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    avisos = pd.read_excel(os.path.join(DATA_DIR, "historico_avisos_proc.xlsx"))
    equipos = pd.read_excel(os.path.join(DATA_DIR, "equipos_proc.xlsx"))

    equipos = equipos[["Equipo", "Torre", "Linea", "Departamento", "Municipio", "CTE"]]

    df = avisos.merge(equipos, on="Equipo", how="left")

    # Filas sin equipo asociado en el catálogo (no aportan geografía) -> se marcan
    df["Departamento"] = df["Departamento"].fillna("Sin dato")
    df["CTE"] = df["CTE"].fillna("Sin dato")

    return df


def departamentos_disponibles() -> list:
    df = load_data()
    return sorted(df["Departamento"].dropna().unique().tolist())


def ctes_disponibles() -> list:
    df = load_data()
    return sorted(df["CTE"].dropna().unique().tolist())
