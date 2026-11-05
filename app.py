"""QR Eventos — prueba 1.

Rutas (por parámetro en la URL):
  /                 -> el artista crea su invitación y obtiene link + QR para compartir
  /?a=<código>      -> el seguidor se registra y obtiene su QR personal
  /?p=privacidad    -> política de tratamiento de datos
"""
import hmac
import re
from datetime import date

import streamlit as st

try:
    from streamlit_qrcode_scanner import qrcode_scanner
except ImportError:  # el escáner continuo es opcional
    qrcode_scanner = None

from config import (
    APP_NAME,
    POLITICA_VERSION,
    QR_PERSONAL_PREFIX,
    REDES_SOCIALES,
)
from core import mailer, sheets
from core.lector import leer_qr_de_imagen, normalizar_codigo
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
        enviar = st.form_submit_button("Generar mi QR", type="primary", width="stretch")

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
            width="stretch",
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
        enviar = st.form_submit_button("Obtener mi QR", type="primary", width="stretch")

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
                registro["email_enviado"] = enviar_correo(registro, inv)
                sheets.crear_registro(registro)
        st.session_state[clave_resultado] = registro
        st.rerun()
    except Exception as e:
        mostrar_error_conexion(e)


def enviar_correo(registro: dict, inv: dict) -> str:
    """Envía el QR por correo. Devuelve el estado para la hoja: SI / ERROR / NO_CONFIGURADO."""
    if not mailer.correo_configurado():
        return "NO_CONFIGURADO"
    try:
        mailer.enviar_qr(
            destino=registro["email"],
            nombre=registro["nombre"].split()[0],
            evento=inv["evento"],
            artista=inv["artista"],
            fecha=str(inv.get("fecha_evento", "")),
            beneficio=str(inv.get("beneficio", "")),
            codigo=registro["registro_id"],
            qr_png_bytes=qr_png(f"{QR_PERSONAL_PREFIX}{registro['registro_id']}", box_size=12),
        )
        return "SI"
    except Exception as e:
        st.session_state["error_correo"] = f"{type(e).__name__}: {e}"
        return "ERROR"


def mostrar_qr_personal(registro: dict, inv: dict):
    if st.session_state.get(f"ya_registrado_{inv['invitacion_id']}"):
        st.info("Ya estabas registrado con este correo. Este es tu QR.")
    else:
        st.success(f"¡Listo, {registro['nombre'].split()[0]}! Este es tu QR personal.")
        estado = registro.get("email_enviado")
        if estado == "SI":
            st.write(f"📧 También te lo enviamos a **{registro['email']}**. "
                     "Si no lo ves, revisa la carpeta de spam.")
        elif estado == "ERROR":
            st.warning("No pudimos enviarte el correo. Descarga el QR o toma un pantallazo.")
    contenido = f"{QR_PERSONAL_PREFIX}{registro['registro_id']}"
    st.image(qr_png(contenido), width=280)
    st.write(f"Código: **{registro['registro_id']}**")
    st.download_button(
        "Descargar mi QR (PNG)",
        data=qr_png(contenido, box_size=16),
        file_name=f"mi_qr_{registro['registro_id']}.png",
        mime="image/png",
        width="stretch",
    )
    if mailer.correo_configurado():
        clave = f"reenviado_{registro['registro_id']}"
        if st.button("Enviármelo de nuevo por correo", width="stretch",
                     disabled=st.session_state.get(clave, False)):
            with st.spinner("Enviando..."):
                estado = enviar_correo(registro, inv)
            if estado == "SI":
                st.session_state[clave] = True  # un reenvío por sesión
                st.success(f"Enviado a {registro['email']}.")
            else:
                st.warning("No pudimos enviar el correo. Intenta más tarde.")
    st.caption(
        "Descárgalo o toma un pantallazo y muéstralo en la entrada. Es personal: "
        "solo sirve para un ingreso."
    )


# ---------------------------------------------------------------------------
# Página: puerta (check-in)
# ---------------------------------------------------------------------------
def pagina_puerta():
    st.title("🚪 Puerta")

    clave_ok = _secret("PUERTA_CLAVE")
    if not clave_ok:
        st.error("Falta configurar PUERTA_CLAVE en los secrets.")
        return
    if not st.session_state.get("puerta_ok"):
        with st.form("form_clave"):
            clave = st.text_input("Clave de puerta", type="password")
            entrar = st.form_submit_button("Entrar", type="primary", width="stretch")
        if entrar:
            if hmac.compare_digest(clave.encode(), str(clave_ok).encode()):
                st.session_state["puerta_ok"] = True
                st.rerun()
            else:
                st.error("Clave incorrecta.")
        return

    try:
        lista_eventos = sheets.eventos()
    except Exception as e:
        mostrar_error_conexion(e)
        return
    if not lista_eventos:
        st.info("Todavía no hay eventos con invitaciones.")
        return
    evento = st.selectbox("Evento", lista_eventos, key="puerta_evento")

    tab_scan, tab_foto, tab_manual = st.tabs(["📷 Escanear", "🖼️ Foto", "⌨️ Código"])
    leido = None
    with tab_scan:
        if qrcode_scanner is None:
            st.warning("El escáner continuo no está disponible. Usa Foto o Código.")
        else:
            st.caption("Apunta la cámara al QR. Lee solo; no hay que oprimir nada.")
            valor = qrcode_scanner(key="scanner")
            # El componente devuelve el último QR leído en cada recarga:
            # solo procesamos cuando cambia.
            if valor and valor != st.session_state.get("ultimo_scan"):
                st.session_state["ultimo_scan"] = valor
                leido = valor
    with tab_foto:
        foto = st.camera_input("Toma una foto del QR", label_visibility="collapsed")
        if foto is not None and foto.file_id != st.session_state.get("ultima_foto"):
            st.session_state["ultima_foto"] = foto.file_id
            leido = leer_qr_de_imagen(foto.getvalue()) or ""
            if not leido:
                st.warning("No se encontró un QR en la foto. Acércala y vuelve a intentar.")
                leido = None
    with tab_manual:
        with st.form("form_codigo", clear_on_submit=True):
            escrito = st.text_input("Código del QR", placeholder="Ej: F5MZJ7PVHP")
            if st.form_submit_button("Validar", width="stretch") and escrito:
                leido = escrito

    if leido is not None:
        codigo = normalizar_codigo(leido)
        if codigo is None:
            st.session_state["puerta_resultado"] = ("INVALIDO", None, leido)
        else:
            try:
                estado, registro = sheets.registrar_checkin(codigo, evento)
                st.session_state["puerta_resultado"] = (estado, registro, codigo)
            except Exception as e:
                mostrar_error_conexion(e)

    mostrar_resultado_puerta(st.session_state.get("puerta_resultado"))

    st.divider()
    c1, c2 = st.columns([3, 1])
    c1.subheader("Asistencia por artista")
    if c2.button("Actualizar", width="stretch"):
        pass  # el clic recarga la página y el resumen se lee de nuevo
    try:
        resumen = sheets.resumen_evento(evento)
    except Exception as e:
        mostrar_error_conexion(e)
        return
    if not resumen:
        st.caption("Aún no hay registros para este evento.")
        return
    m1, m2 = st.columns(2)
    m1.metric("Ingresaron", sum(r["Ingresaron"] for r in resumen))
    m2.metric("Registrados", sum(r["Registrados"] for r in resumen))
    st.dataframe(resumen, hide_index=True, width="stretch")


def mostrar_resultado_puerta(resultado):
    if not resultado:
        return
    estado, reg, codigo = resultado
    if estado == "OK":
        st.success(f"### ✅ Bienvenido/a, {reg['nombre']}\n"
                   f"Viene por **{reg['artista']}** · código {codigo}")
    elif estado == "YA_INGRESO":
        st.error(f"### ⛔ Este QR ya ingresó\n"
                 f"{reg['nombre']} ({reg['artista']}) entró a las **{reg['checkin_hora']}**.")
    elif estado == "OTRO_EVENTO":
        st.warning(f"### ⚠️ QR de otro evento\n"
                   f"{reg['nombre']} está registrado para **{reg['evento']}**.")
    elif estado == "NO_EXISTE":
        st.error(f"### ❌ Código no encontrado\n`{codigo}` no está registrado.")
    else:
        st.error("### ❌ Este QR no es de QR Eventos")


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
elif params.get("p") == "puerta":
    pagina_puerta()
elif params.get("a"):
    pagina_seguidor(params["a"])
else:
    pagina_artista()
