"""Texto de la política de tratamiento de datos (Ley 1581 de 2012, Colombia).

IMPORTANTE: es una plantilla base para la prueba. Antes de usarla con público
real, revísala con un abogado y completa los datos del responsable.
"""


def texto_politica(responsable: str, contacto: str, version: str) -> str:
    return f"""
### Política de tratamiento de datos personales

**Versión:** {version}

**Responsable del tratamiento:** {responsable}. Contacto: {contacto}.

**Datos que recogemos:** nombre, correo electrónico y número de celular.

**Para qué los usamos:**
1. Generar tu código QR personal para el evento.
2. Verificar tu ingreso al evento y aplicar el beneficio o descuento ofrecido.
3. Contar cuántos asistentes llegaron por invitación de cada artista.
4. Enviarte información relacionada con el evento al que te registraste.

**Con quién los compartimos:** el artista que te invitó y el organizador del
evento reciben solo el **número** de personas registradas y asistentes, no tus
datos personales. No vendemos tus datos.

**Tus derechos (Ley 1581 de 2012):** puedes conocer, actualizar, rectificar y
pedir que eliminemos tus datos, o revocar esta autorización, escribiendo a
{contacto}. También puedes presentar quejas ante la Superintendencia de
Industria y Comercio.

**Conservación:** guardamos tus datos mientras dure la finalidad descrita y
luego los eliminamos o anonimizamos.

Al marcar la casilla de aceptación autorizas de forma previa, expresa e
informada el tratamiento de tus datos para las finalidades descritas.
"""
