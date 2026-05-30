"""
Gems guarda los parametros distribuidos en varios archivos.
No es muy claro exactamente en que archivo esta cada parametro.
Este script es una utilidad para encontrar en que archivo .csv esta cada parametro de interes
Los resultados de la busqueda se guardan en search_result.json
"""
import pandas as pd
import numpy as np
import os
from pathlib import Path
import json
from tqdm import tqdm

PARAM_TARGET_LIST = "params_of_interest.txt"
FILES_DIR = Path("../GFQA_v3")

def find_param_in_files(param_list):
    param_files = {}
    all_files = [f for f in os.listdir(FILES_DIR) if "metadata" not in f]

    for p_code in tqdm(param_list, desc="Parameters", unit="param"):
        param_files[p_code] = []
        for file in tqdm(all_files, desc=f"  [{p_code}]", unit="file", leave=False):
            try:
                dff = pd.read_csv(FILES_DIR / file, encoding="ISO-8859-1", low_memory=False)
                if np.sum((dff["Parameter Code"] == p_code).astype(np.int32)) > 0:
                    param_files[p_code].append(file)
            except Exception:
                continue

    return param_files


if __name__ == '__main__':
    with open(PARAM_TARGET_LIST, "r") as f:
        params = f.read().splitlines()

    param_files = find_param_in_files(params)

    with open("search_result.json", "w") as f:
        f.write(json.dumps(param_files, indent=4))