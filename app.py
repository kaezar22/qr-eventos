"""QR Eventos — prueba 1.

Rutas (por parámetro en la URL):
  /                 -> el artista crea su invitación y obtiene link + QR para compartir
  /?a=<código>      -> el seguidor se registra y obtiene su QR personal
  /?p=privacidad    -> política de tratamiento de datos
"""
import re
from datetime import date

import streamlit as st

from config import (
    APP_NAME,
    POLITICA_VERSION,
    QR_PERSONAL_PREFIX,
    REDES_SOCIALES,
)
from core import sheets
from core.politica import texto_politica
from core.qr import nuevo_id, qr_png

st.set_page_config(page_title=APP_NAME, page_icon="🎟️", layout="centered")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def base_url() -> str:
    """URL pública de la app. En Streamlit Cloud define BASE_URL en secrets."""
    url = _secret("BASE_URL")
    if not url:
        try:
            url = st.context.url or ""
        except Exception:
            url = ""
    url = url.split("?")[0].rstrip("/")
    return url or "http://localhost:8501"


def limpiar_celular(valor: str) -> str:
    return re.sub(r"[^\d+]", "", valor or "")


def celular_valido(valor: str) -> bool:
    digitos = re.sub(r"\D", "", valor)
    return 7 <= len(digitos) <= 15


def mostrar_error_conexion(e: Exception):
    st.error("No pudimos conectarnos con la base de datos. Intenta de nuevo en un momento.")
    with st.expander("Detalle técnico"):
        st.code(f"{type(e).__name__}: {e}")


def politica_md() -> str:
    return texto_politica(
        responsable=_secret("RESPONSABLE_NOMBRE", "Hayaku Lab"),
        contacto=_secret("RESPONSABLE_EMAIL", "[correo de contacto]"),
        version=POLITICA_VERSION,
    )


# ---------------------------------------------------------------------------
# Página: artista
# ---------------------------------------------------------------------------
def pagina_artista():
    st.title("🎟️ Invita a tus seguidores")
    st.write(
        "Crea tu invitación para el evento. Te damos un **link y un QR** para "
        "compartir en TikTok o Instagram. Cada seguidor que se registre recibe "
        "su propio QR y queda contado a tu nombre."
    )

    with st.form("form_artista"):
        artista = st.text_input("Nombre artístico *")
        c1, c2 = st.columns([1, 2])
        red = c1.selectbox("Red social", REDES_SOCIALES)
        usuario = c2.text_input("Usuario", placeholder="@tu_usuario")
        email = st.text_input("Tu correo *")
        evento = st.text_input("Nombre del evento *")
        fecha = st.date_input("Fecha del evento", value=date.today(), format="YYYY-MM-DD")
        beneficio = st.text_input(
            "Beneficio para tus seguidores",
            placeholder="Ej: 10% de descuento en consumo",
        )
        enviar = st.form_submit_button("Generar mi QR", type="primary", use_container_width=True)

    if enviar:
        errores = []
        if not artista.strip():
            errores.append("Escribe tu nombre artístico.")
        if not EMAIL_RE.match(email.strip()):
            errores.append("Escribe un correo válido.")
        if not evento.strip():
            errores.append("Escribe el nombre del evento.")
        for e in errores:
            st.error(e)
        if not errores:
            invitacion = {
                "invitacion_id": nuevo_id(6),
                "artista": artista.strip(),
                "red_social": red,
                "usuario_red": usuario.strip(),
                "email_artista": email.strip().lower(),
                "evento": evento.strip(),
                "fecha_evento": fecha.isoformat(),
                "beneficio": beneficio.strip(),
            }
            try:
                with st.spinner("Creando tu invitación..."):
                    sheets.crear_invitacion(invitacion)
                st.session_state["invitacion_creada"] = invitacion
            except Exception as e:
                mostrar_error_conexion(e)

    inv = st.session_state.get("invitacion_creada")
    if inv:
        link = f"{base_url()}/?a={inv['invitacion_id']}"
        st.success(f"¡Listo, {inv['artista']}! Comparte este link o este QR.")
        st.image(qr_png(link), width=280)
        st.code(link, language=None)
        st.download_button(
            "Descargar QR (PNG)",
            data=qr_png(link, box_size=16),
            file_name=f"qr_{inv['artista']}_{inv['invitacion_id']}.png".replace(" ", "_"),
            mime="image/png",
            use_container_width=True,
        )
        st.caption(
            f"Código de tu invitación: **{inv['invitacion_id']}**. Guárdalo: con él "
            "sabremos cuántas personas llegaron por ti."
        )


# ---------------------------------------------------------------------------
# Página: seguidor
# ---------------------------------------------------------------------------
def pagina_seguidor(invitacion_id: str):
    try:
        inv = sheets.buscar_invitacion(invitacion_id)
    except Exception as e:
        mostrar_error_conexion(e)
        return

    if not inv or str(inv.get("activa", "SI")).upper() != "SI":
        st.title("Invitación no encontrada")
        st.write("Revisa el link que te compartieron o pídele uno nuevo al artista.")
        return

    st.title(f"🎟️ {inv['evento']}")
    usuario = f" ({inv['usuario_red']})" if inv.get("usuario_red") else ""
    st.subheader(f"Invitación de {inv['artista']}{usuario}")
    if inv.get("fecha_evento"):
        st.write(f"📅 {inv['fecha_evento']}")
    if inv.get("beneficio"):
        st.info(f"🎁 Tu beneficio: **{inv['beneficio']}**")

    clave_resultado = f"registro_{inv['invitacion_id']}"
    if st.session_state.get(clave_resultado):
        mostrar_qr_personal(st.session_state[clave_resultado], inv)
        return

    st.write("Regístrate para recibir tu QR personal. Lo mostrarás en la entrada del evento.")
    with st.form("form_seguidor"):
        nombre = st.text_input("Nombre completo *")
        email = st.text_input("Correo electrónico *")
        celular = st.text_input("Celular *", placeholder="300 123 4567")
        with st.expander("Leer la política de tratamiento de datos"):
            st.markdown(politica_md())
        acepta = st.checkbox(
            "Autorizo el tratamiento de mis datos personales según la política "
            "de tratamiento de datos. *"
        )
        enviar = st.form_submit_button("Obtener mi QR", type="primary", use_container_width=True)

    if not enviar:
        return

    celular_limpio = limpiar_celular(celular)
    errores = []
    if not nombre.strip():
        errores.append("Escribe tu nombre.")
    if not EMAIL_RE.match(email.strip()):
        errores.append("Escribe un correo válido.")
    if not celular_valido(celular_limpio):
        errores.append("Escribe un celular válido.")
    if not acepta:
        errores.append("Debes aceptar la política de tratamiento de datos para registrarte.")
    for e in errores:
        st.error(e)
    if errores:
        return

    try:
        with st.spinner("Generando tu QR..."):
            existente = sheets.buscar_registro(inv["invitacion_id"], email)
            if existente:
                registro = existente
                st.session_state[f"ya_registrado_{inv['invitacion_id']}"] = True
            else:
                registro = {
                    "registro_id": nuevo_id(10),
                    "invitacion_id": inv["invitacion_id"],
                    "artista": inv["artista"],
                    "evento": inv["evento"],
                    "nombre": nombre.strip(),
                    "email": email.strip().lower(),
                    "celular": celular_limpio,
                    "acepta_politica": "SI",
                    "version_politica": POLITICA_VERSION,
                }
                sheets.crear_registro(registro)
        st.session_state[clave_resultado] = registro
        st.rerun()
    except Exception as e:
        mostrar_error_conexion(e)


def mostrar_qr_personal(registro: dict, inv: dict):
    if st.session_state.get(f"ya_registrado_{inv['invitacion_id']}"):
        st.info("Ya estabas registrado con este correo. Este es tu QR.")
    else:
        st.success(f"¡Listo, {registro['nombre'].split()[0]}! Este es tu QR personal.")
    contenido = f"{QR_PERSONAL_PREFIX}{registro['registro_id']}"
    st.image(qr_png(contenido), width=280)
    st.write(f"Código: **{registro['registro_id']}**")
    st.download_button(
        "Descargar mi QR (PNG)",
        data=qr_png(contenido, box_size=16),
        file_name=f"mi_qr_{registro['registro_id']}.png",
        mime="image/png",
        use_container_width=True,
    )
    st.caption(
        "Descárgalo o toma un pantallazo y muéstralo en la entrada. Es personal: "
        "solo sirve para un ingreso."
    )


# ---------------------------------------------------------------------------
# Página: política
# ---------------------------------------------------------------------------
def pagina_politica():
    st.markdown(politica_md())


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
params = st.query_params
if params.get("p") == "privacidad":
    pagina_politica()
elif params.get("a"):
    pagina_seguidor(params["a"])
else:
    pagina_artista()
