"""Verifica la conexión con Google Sheets y crea las pestañas si faltan.

Uso:  python check_sheets.py
Lee las credenciales de service_account.json (raíz del repo) o de
.streamlit/secrets.toml, y SPREADSHEET_ID de secrets.toml.
"""
import json
import sys
import tomllib
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from config import INVITACIONES_COLS, REGISTROS_COLS, WS_INVITACIONES, WS_REGISTROS

RAIZ = Path(__file__).resolve().parent
DEFAULT_SHEET = "1C24HefzSLoDiN5TlQ2LKTv4Ot_ktq5SHwEeXjXekofU"


def main():
    secrets = {}
    sp = RAIZ / ".streamlit" / "secrets.toml"
    if sp.exists():
        secrets = tomllib.loads(sp.read_text(encoding="utf-8"))

    if "gcp_service_account" in secrets:
        info = dict(secrets["gcp_service_account"])
    elif "GOOGLE_CREDENTIALS" in secrets:
        info = json.loads(secrets["GOOGLE_CREDENTIALS"])
    elif (RAIZ / "service_account.json").exists():
        info = json.loads((RAIZ / "service_account.json").read_text(encoding="utf-8"))
    else:
        sys.exit("✗ No encontré credenciales (service_account.json o secrets.toml).")

    print("Cuenta de servicio:", info.get("client_email"))
    sheet_id = secrets.get("SPREADSHEET_ID", DEFAULT_SHEET)

    try:
        creds = Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        sh = gspread.authorize(creds).open_by_key(sheet_id)
    except Exception as e:
        print(f"✗ No se pudo abrir la hoja: {type(e).__name__}: {e}")
        if "invalid_grant" in str(e):
            print("  → La clave fue revocada/borrada o la cuenta está deshabilitada.")
        elif "PERMISSION_DENIED" in str(e) or "403" in str(e):
            print("  → Comparte la hoja con el correo de la cuenta de servicio (Editor)"
                  " y habilita la Google Sheets API en el proyecto.")
        sys.exit(1)

    print("✓ Hoja abierta:", sh.title)
    existentes = [ws.title for ws in sh.worksheets()]
    for nombre, cols in [(WS_INVITACIONES, INVITACIONES_COLS), (WS_REGISTROS, REGISTROS_COLS)]:
        if nombre in existentes:
            print(f"✓ Pestaña '{nombre}' ya existe")
        else:
            ws = sh.add_worksheet(title=nombre, rows=1000, cols=len(cols))
            ws.append_row(cols, value_input_option="RAW")
            ws.freeze(rows=1)
            print(f"✓ Pestaña '{nombre}' creada")


if __name__ == "__main__":
    main()
