"""Generación de códigos QR y de identificadores. Sin código de Streamlit."""
import io
import secrets
import string

import qrcode
from qrcode.constants import ERROR_CORRECT_M

# Sin caracteres ambiguos (0/O, 1/l/I) para que se puedan dictar o digitar.
_ALFABETO = "".join(c for c in string.ascii_uppercase + string.digits if c not in "0O1IL")


def nuevo_id(largo: int = 8) -> str:
    """Código aleatorio, difícil de adivinar (8 caracteres ≈ 2^40 combinaciones)."""
    return "".join(secrets.choice(_ALFABETO) for _ in range(largo))


def qr_png(contenido: str, box_size: int = 10) -> bytes:
    """Devuelve un PNG con el QR del contenido dado."""
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=box_size, border=3)
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
