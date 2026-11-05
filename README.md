# QR Eventos

App web (Streamlit) para saber cuántas personas trae cada artista o influencer a un evento.

**Prueba 1 (este repo):**
1. El artista crea su invitación y recibe un **link + QR** para compartir con sus seguidores.
2. El seguidor abre el link, llena sus datos, **acepta la política de tratamiento de datos** y recibe su **QR personal** (único).
3. Todo queda en Google Sheets: pestaña `invitaciones` (artistas) y pestaña `registros` (seguidores).
4. El seguidor recibe además su QR por **correo** (Gmail). La columna `email_enviado` dice SI / ERROR / NO_CONFIGURADO.

Siguientes fases: escáner en la puerta (check-in), canje del descuento, panel por artista y votación.

## Estructura

```
app.py              # interfaz y rutas (/, /?a=<código>, /?p=privacidad)
config.py           # nombres de pestañas, columnas, constantes
core/sheets.py      # lectura/escritura en Google Sheets
core/qr.py          # generación de QR e identificadores
core/mailer.py      # envío del QR por correo (SMTP Gmail)
core/politica.py    # texto de la política de datos (plantilla, revisar con abogado)
check_sheets.py     # prueba la conexión y crea las pestañas
```

## Correr en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # y edítalo
# deja la llave de la cuenta de servicio como service_account.json en la raíz

python check_sheets.py          # verifica acceso y crea pestañas
streamlit run app.py
```

La hoja de Google debe estar compartida (Editor) con el `client_email` de la cuenta de servicio, y el proyecto de Google Cloud debe tener habilitada la **Google Sheets API**.

## Subir a GitHub

`service_account.json` y `.streamlit/secrets.toml` están en `.gitignore`: **no se suben**.

```bash
git init
git add .
git status                      # confirma que no aparece ninguna credencial
git commit -m "QR Eventos: prueba 1"
git branch -M main
git remote add origin https://github.com/<usuario>/qr_eventos.git
git push -u origin main
```

## Publicar en Streamlit Cloud

1. New app → repo `qr_eventos`, archivo `app.py`.
2. En **Settings → Secrets** pega el contenido de `secrets.toml.example` con:
   - `BASE_URL` = la URL pública de la app (ej. `https://qr-eventos.streamlit.app`), para que el link del artista sea correcto.
   - la sección `[email]` con la cuenta de Gmail y su contraseña de aplicación.
   - la sección `[gcp_service_account]` con los campos del JSON de la cuenta de servicio.

## Datos en la hoja

**invitaciones:** invitacion_id, creado, artista, red_social, usuario_red, email_artista, evento, fecha_evento, beneficio, activa

**registros:** registro_id, creado, invitacion_id, artista, evento, nombre, email, celular, acepta_politica, version_politica, checkin, checkin_hora, descuento_usado, descuento_hora, email_enviado

El QR personal contiene `QREV:<registro_id>`; el escáner de la fase 2 usará ese código para marcar `checkin` y `descuento_usado`.

Un mismo correo solo se registra una vez por invitación: si repite, recibe el mismo QR.
