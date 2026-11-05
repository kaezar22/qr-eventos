"""Configuración central de QR Eventos."""

APP_NAME = "QR Eventos"

# ---------------------------------------------------------------------------
# Google Sheets: nombres de pestañas y columnas (el orden importa al escribir)
# ---------------------------------------------------------------------------
WS_INVITACIONES = "invitaciones"
WS_REGISTROS = "registros"

INVITACIONES_COLS = [
    "invitacion_id",     # código corto del link del artista (va en ?a=...)
    "creado",            # fecha-hora (Bogotá)
    "artista",           # nombre artístico
    "red_social",        # TikTok / Instagram / ...
    "usuario_red",       # @usuario
    "email_artista",
    "evento",
    "fecha_evento",
    "beneficio",         # texto del descuento / beneficio
    "activa",            # SI / NO
]

REGISTROS_COLS = [
    "registro_id",       # código único del QR personal
    "creado",
    "invitacion_id",
    "artista",
    "evento",
    "nombre",
    "email",
    "celular",
    "acepta_politica",   # SI
    "version_politica",
    # --- columnas para las siguientes fases (puerta y descuento) ---
    "checkin",           # vacío / SI
    "checkin_hora",
    "descuento_usado",   # vacío / SI
    "descuento_hora",
    "email_enviado",     # SI / ERROR / NO_CONFIGURADO
]

# ---------------------------------------------------------------------------
# Política de datos
# ---------------------------------------------------------------------------
POLITICA_VERSION = "v1-2026-11"

# Prefijo del contenido del QR personal. El escáner de la puerta (fase 2)
# leerá "QREV:<registro_id>".
QR_PERSONAL_PREFIX = "QREV:"

REDES_SOCIALES = ["TikTok", "Instagram", "YouTube", "X / Twitter", "Otra"]

TIMEZONE = "America/Bogota"
