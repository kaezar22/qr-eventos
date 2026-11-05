"""Envío del QR personal por correo (SMTP, por defecto Gmail). Sin UI de Streamlit.

Configuración en secrets:
  [email]
  SMTP_USER = "cuenta@gmail.com"
  SMTP_PASSWORD = "contraseña de aplicación (16 letras)"
  FROM_NAME = "QR Eventos"
  # opcionales: SMTP_HOST (smtp.gmail.com), SMTP_PORT (465), SMTP_SSL (true)
"""
import html
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import streamlit as st


def _config() -> dict | None:
    try:
        cfg = dict(st.secrets["email"])
    except Exception:
        return None
    if not cfg.get("SMTP_USER") or not cfg.get("SMTP_PASSWORD"):
        return None
    return cfg


def correo_configurado() -> bool:
    return _config() is not None


def _html(nombre: str, evento: str, artista: str, fecha: str,
          beneficio: str, codigo: str, cid: str) -> str:
    e = html.escape
    fila_fecha = f"<p style='margin:4px 0'>📅 {e(fecha)}</p>" if fecha else ""
    fila_beneficio = (
        f"<p style='background:#EEF2FF;padding:10px 14px;border-radius:8px'>"
        f"🎁 Tu beneficio: <b>{e(beneficio)}</b></p>" if beneficio else ""
    )
    return f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:auto;color:#222">
  <h2 style="margin-bottom:4px">🎟️ {e(evento)}</h2>
  <p style="margin:4px 0">Invitación de <b>{e(artista)}</b></p>
  {fila_fecha}
  <p>Hola {e(nombre)}, este es tu QR personal. Muéstralo en la entrada del evento.</p>
  {fila_beneficio}
  <p style="text-align:center"><img src="cid:{cid[1:-1]}" width="260" height="260"
     alt="Tu código QR" style="border:1px solid #ddd"></p>
  <p style="text-align:center;font-size:18px">Código: <b>{e(codigo)}</b></p>
  <p style="font-size:12px;color:#666">Es personal y sirve para un solo ingreso.
  También va adjunto como imagen por si no se ve arriba.</p>
</div>"""


def enviar_qr(destino: str, nombre: str, evento: str, artista: str, fecha: str,
              beneficio: str, codigo: str, qr_png_bytes: bytes) -> None:
    """Envía el correo. Lanza excepción si falla."""
    cfg = _config()
    if cfg is None:
        raise RuntimeError("Correo no configurado (falta [email] en secrets).")

    msg = EmailMessage()
    msg["Subject"] = f"Tu QR para {evento}"
    msg["From"] = formataddr((cfg.get("FROM_NAME", "QR Eventos"), cfg["SMTP_USER"]))
    msg["To"] = destino
    msg.set_content(
        f"Hola {nombre},\n\nEste es tu QR personal para {evento} "
        f"(invitación de {artista}).\nCódigo: {codigo}\n"
        + (f"Tu beneficio: {beneficio}\n" if beneficio else "")
        + "\nMuestra el QR adjunto en la entrada. Es personal y sirve para un solo ingreso.\n"
    )
    cid = make_msgid(domain="qr-eventos")
    msg.add_alternative(
        _html(nombre, evento, artista, fecha, beneficio, codigo, cid), subtype="html"
    )
    msg.get_payload()[1].add_related(qr_png_bytes, "image", "png", cid=cid)
    msg.add_attachment(qr_png_bytes, maintype="image", subtype="png",
                       filename=f"mi_qr_{codigo}.png")

    host = cfg.get("SMTP_HOST", "smtp.gmail.com")
    port = int(cfg.get("SMTP_PORT", 465))
    usar_ssl = str(cfg.get("SMTP_SSL", "true")).lower() != "false"
    smtp_cls = smtplib.SMTP_SSL if usar_ssl else smtplib.SMTP
    with smtp_cls(host, port, timeout=20) as s:
        if cfg.get("SMTP_PASSWORD") != "-":  # "-" = servidor de prueba sin login
            s.login(cfg["SMTP_USER"], str(cfg["SMTP_PASSWORD"]).replace(" ", ""))
        s.send_message(msg)
