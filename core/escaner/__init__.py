"""Escáner de QR continuo con selector de cámara (componente propio de Streamlit).

Usa html5-qrcode 2.3.8 (Apache-2.0), incluido en frontend/.
Devuelve {"text": <contenido del QR>, "ts": <milisegundos>} cada vez que lee un QR.
El mismo QR puede volver a leerse después de 3 segundos (útil para detectar reingresos).
"""
from pathlib import Path

import streamlit.components.v1 as components

_componente = components.declare_component(
    "escaner_qr", path=str(Path(__file__).parent / "frontend")
)


def escaner_qr(key: str | None = None) -> dict | None:
    return _componente(key=key, default=None)
