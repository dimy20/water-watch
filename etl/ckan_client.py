import requests
import urllib3

CATALOGOS_API = "https://catalogodatos.gub.uy/api/3/action"


def package_search(package: str) -> list[dict]:
    """Devuelve los resources del dataset CKAN cuyo nombre coincide exactamente con `package`."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    resp = requests.get(
        f"{CATALOGOS_API}/package_search",
        params={"q": package},
        verify=False,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"CKAN respondio success=False para {package}: {data}")

    resources = []
    for result in data["result"]["results"]:
        if result.get("name") == package:
            resources.extend(result.get("resources", []))
    return resources


def download_resource(resource: dict) -> bytes:
    """Descarga el contenido del resource CKAN."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    resp = requests.get(resource["url"], verify=False, timeout=120)
    resp.raise_for_status()
    return resp.content
