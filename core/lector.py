"""Lectura de QR desde una foto y normalización del código. Sin UI de Streamlit."""
import re

from config import QR_PERSONAL_PREFIX

_CODIGO_RE = re.compile(r"^[A-Z0-9]{6,12}$")


def normalizar_codigo(texto: str | None) -> str | None:
    """Acepta 'QREV:ABC123XYZ9' o solo 'ABC123XYZ9'. Devuelve el código o None."""
    if not texto:
        return None
    t = texto.strip().upper().replace(" ", "")
    if t.startswith(QR_PERSONAL_PREFIX):
        t = t[len(QR_PERSONAL_PREFIX):]
    return t if _CODIGO_RE.match(t) else None


def leer_qr_de_imagen(imagen_bytes: bytes) -> str | None:
    """Decodifica el primer QR de una imagen (JPG/PNG). None si no encuentra."""
    import cv2  # import diferido: solo se carga si se usa la foto
    import numpy as np

    img = cv2.imdecode(np.frombuffer(imagen_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    detector = cv2.QRCodeDetector()
    for candidata in (img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)):
        texto, _, _ = detector.detectAndDecode(candidata)
        if texto:
            return texto
    return None
