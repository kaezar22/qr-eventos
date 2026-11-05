"""Genera cloud_secrets.toml para pegar en Streamlit Cloud (Settings > Secrets).

Uso:  python make_cloud_secrets.py
Junta .streamlit/secrets.toml + service_account.json en un solo archivo.
cloud_secrets.toml está en .gitignore: no se sube a GitHub.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
local = RAIZ / ".streamlit" / "secrets.toml"
llave = RAIZ / "service_account.json"
salida = RAIZ / "cloud_secrets.toml"

texto = local.read_text(encoding="utf-8").rstrip() + "\n" if local.exists() else ""
if "[gcp_service_account]" not in texto:
    info = json.loads(llave.read_text(encoding="utf-8"))
    # json.dumps produce strings válidos en TOML (escapa \n de la private_key)
    texto += "\n[gcp_service_account]\n"
    texto += "".join(f"{k} = {json.dumps(v)}\n" for k, v in info.items())

salida.write_text(texto, encoding="utf-8")
print(f"✓ Generado {salida.name}. Ábrelo, copia todo y pégalo en Streamlit Cloud > Secrets.")
if 'BASE_URL = ""' in texto:
    print("  Recuerda: en Streamlit Cloud cambia BASE_URL por la URL pública de la app.")
