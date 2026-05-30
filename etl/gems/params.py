import json

with open("./scripts/search_result.json") as f:
    _raw = json.load(f)

IN_SITU = {code: files[0] for code, files in _raw.items()}

REMOTE_SENSING = {
    "TURB":  "Optical.csv",
    "TSS":   "Water.csv",
    "Chl-a": "Pigment.csv",
    "TRANS": "Optical.csv",
}
