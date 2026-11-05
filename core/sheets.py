"""Toda la lectura/escritura en Google Sheets vive aquí. Sin UI de Streamlit.

Credenciales (en este orden):
  1. st.secrets["gcp_service_account"]  -> tabla TOML (recomendado en Streamlit Cloud)
  2. st.secrets["GOOGLE_CREDENTIALS"]   -> JSON como texto (mismo formato que analyzer_3.0)
  3. archivo service_account.json en la raíz del repo (solo para desarrollo local)
"""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

from config import (
    INVITACIONES_COLS,
    REGISTROS_COLS,
    TIMEZONE,
    WS_INVITACIONES,
    WS_REGISTROS,
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
LOCAL_KEY_FILE = Path(__file__).resolve().parent.parent / "service_account.json"


def ahora() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")


def _secret(name, default=None):
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError, Exception):
        return default


def _credenciales_info() -> dict:
    tabla = _secret("gcp_service_account")
    if tabla:
        return dict(tabla)
    texto = _secret("GOOGLE_CREDENTIALS")
    if texto:
        return json.loads(texto)
    if LOCAL_KEY_FILE.exists():
        return json.loads(LOCAL_KEY_FILE.read_text(encoding="utf-8"))
    raise RuntimeError(
        "No hay credenciales de Google. Agrega [gcp_service_account] en "
        ".streamlit/secrets.toml o deja service_account.json en la raíz del repo."
    )


def spreadsheet_id() -> str:
    sid = _secret("SPREADSHEET_ID")
    if not sid:
        raise RuntimeError("Falta SPREADSHEET_ID en .streamlit/secrets.toml")
    return sid


@st.cache_resource(show_spinner=False)
def _spreadsheet():
    creds = Credentials.from_service_account_info(_credenciales_info(), scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(spreadsheet_id())


def _hoja(nombre: str, columnas: list[str]):
    """Devuelve la pestaña; si no existe la crea con encabezados."""
    sh = _spreadsheet()
    try:
        ws = sh.worksheet(nombre)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=nombre, rows=1000, cols=len(columnas))
        ws.append_row(columnas, value_input_option="RAW")
        ws.freeze(rows=1)
        return ws
    encabezado = ws.row_values(1)
    if not encabezado:
        ws.update([columnas], "A1")
        ws.freeze(rows=1)
    elif encabezado != columnas and columnas[: len(encabezado)] == encabezado:
        # Se agregaron columnas nuevas al final (p. ej. email_enviado): actualizar encabezado.
        if ws.col_count < len(columnas):
            ws.add_cols(len(columnas) - ws.col_count)
        ws.update([columnas], "A1")
    return ws


def _append(nombre: str, columnas: list[str], fila: dict):
    ws = _hoja(nombre, columnas)
    # RAW: lo que escribe el usuario nunca se interpreta como fórmula.
    ws.append_row([str(fila.get(c, "")) for c in columnas], value_input_option="RAW")


@st.cache_data(ttl=60, show_spinner=False)
def _leer(nombre: str, columnas: tuple) -> list[dict]:
    ws = _hoja(nombre, list(columnas))
    return ws.get_all_records(expected_headers=list(columnas), default_blank="")


# ---------------------------------------------------------------------------
# Invitaciones (link/QR que comparte el artista)
# ---------------------------------------------------------------------------
def crear_invitacion(datos: dict) -> None:
    datos = {**datos, "creado": ahora(), "activa": "SI"}
    _append(WS_INVITACIONES, INVITACIONES_COLS, datos)
    _leer.clear()


def buscar_invitacion(invitacion_id: str) -> dict | None:
    invitacion_id = (invitacion_id or "").strip().upper()
    for intento in range(2):  # si no está en caché, recarga una vez
        for fila in _leer(WS_INVITACIONES, tuple(INVITACIONES_COLS)):
            if str(fila["invitacion_id"]).upper() == invitacion_id:
                return fila
        if intento == 0:
            _leer.clear()
    return None


# ---------------------------------------------------------------------------
# Registros (seguidores)
# ---------------------------------------------------------------------------
def buscar_registro(invitacion_id: str, email: str) -> dict | None:
    """Un seguidor solo puede registrarse una vez por invitación (mismo email)."""
    _leer.clear()
    email = email.strip().lower()
    for fila in _leer(WS_REGISTROS, tuple(REGISTROS_COLS)):
        if fila["invitacion_id"] == invitacion_id and str(fila["email"]).lower() == email:
            return fila
    return None


def crear_registro(datos: dict) -> None:
    datos = {**datos, "creado": ahora()}
    _append(WS_REGISTROS, REGISTROS_COLS, datos)
    _leer.clear()


def verificar_conexion() -> str:
    """Abre la hoja y crea las pestañas si faltan. Devuelve el título."""
    sh = _spreadsheet()
    _hoja(WS_INVITACIONES, INVITACIONES_COLS)
    _hoja(WS_REGISTROS, REGISTROS_COLS)
    return sh.title
