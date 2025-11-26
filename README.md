# MatriSchol - Entrega SENA

Este documento explica cómo instalar, ejecutar y demostrar los flujos clave solicitados para la entrega (solicitudes, aprobaciones/rechazos, notificaciones y logs de correo).

---
## Resumen de funcionalidades entregadas
- Gestión de solicitudes de institución y de cursos (crear, revisar, aprobar, rechazar, solicitar información).
- Notificaciones en panel (`AdminNotification`) y envío de correos en eventos clave (solicitudes, cambios de estado, registro de estudiantes, subida de documentos, matrículas). Todos los envíos quedan registrados en `EmailLog`.
- Control de roles: `admin`/`administrator` (admins globales) y `administrativo` (administrativo de institución). Interfaz oculta botones de acción según rol.
- Seguridad básica: contraseñas almacenadas hasheadas y flujo de login funcionando.
- Lectura de variables de entorno desde `.env`.

---
## Requisitos previos
- Windows (PowerShell 5.1).
- Python 3.10 o superior.
- Base de datos (configurada en `settings.py`).

---
## Instalación y puesta en marcha (PowerShell)
```powershell
# activar el entorno virtual del proyecto
& .\.venv\Scripts\Activate.ps1

# instalar dependencias (si existe requirements.txt)
pip install -r requirements.txt

# aplicar migraciones
python manage.py migrate

# crear superusuario
python manage.py createsuperuser

# ejecutar servidor de desarrollo
python manage.py runserver
```

Accede a `http://127.0.0.1:8000/` y al panel admin en `/admin`.

---
## Ejemplo mínimo de `.env`
Crea `.env` en la raíz del proyecto con al menos las siguientes variables:

```
DEBUG=True
SITE_URL=http://127.0.0.1:8000
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=matrischol.app@gmail.com
EMAIL_HOST_PASSWORD=<tu_app_password>
DEFAULT_FROM_EMAIL="MatriSchol <matrischol.app@gmail.com>"
ADMIN_ALERT_EMAILS=support@example.com,alerts@example.com
```

> Para pruebas locales, usa una contraseña de aplicación (Gmail) o el backend `console.EmailBackend` si no quieres enviar correos reales.

---
## Flujo de demostración (pasos sugeridos para la presentación)
1. Crear/registrar un usuario (o usar `createsuperuser` para el admin).
2. Como `acudiente` o usuario solicitante: crear una Solicitud de Institución o Solicitud de Cursos desde la interfaz.
3. Como `admin`: ir a `Solicitudes` → abrir la solicitud → elegir `Aprobar` / `Solicitar información` / `Rechazar` y añadir comentario.
4. Verificar:
   - Notificación en panel del solicitante.
   - Entrada en `EmailLog` con `exito=True` para el correo enviado.

### Comandos útiles para comprobar EmailLog
```powershell
& .\.venv\Scripts\Activate.ps1
python manage.py shell
```
En el shell python:
```python
from communications.models import EmailLog
for e in EmailLog.objects.order_by('-id_email_log')[:10]:
    print(e.id_email_log, e.destinatario, e.asunto, e.exito, e.error, e.fch_envio)
```

---
## Tests
Para ejecutar la suite de tests (si existen):
```powershell
& .\.venv\Scripts\Activate.ps1
python manage.py test
```
> Nota: en este proyecto la ejecución de `test` puede devolver `0 tests run` si no hay tests definidos. Si deseas, puedo añadir 2-3 pruebas básicas para cubrir los flujos clave.

---
## Archivos relevantes
- `adminpanel/views.py` — vistas y lógica de aprobación/rechazo para solicitudes.
- `communications/email_utils.py` — helpers para enviar emails y registrar en `EmailLog`.
- `templates/email/` — plantillas HTML y TXT para los correos.
- `adminpanel/models.py` y `communications/models.py` — modelos principales.

---
## Recomendaciones para la entrega
- Incluye capturas de pantalla que muestren:
  - Creación de solicitud (formulario completado).
  - Admin revisando y aprobando/rechazando con comentarios.
  - Salida de `EmailLog` donde se vea `exito=True`.
- Mantén `DEBUG=True` solo para demo local; para producción pone `DEBUG=False` y configura `ALLOWED_HOSTS`.

---
## Opcional / Mejoras no obligatorias
- Configurar SPF/DKIM/DMARC en DNS (mejora entregabilidad del correo).
- Procesar correos en background con Celery o RQ para evitar bloquear peticiones.
- Añadir pruebas unitarias para los flujos (puedo generarlas si quieres).

---
## ¿Quieres que haga esto por ti?
Puedo:
- Generar un fixture con datos de ejemplo y un admin de demo.
- Añadir 2–3 tests básicos y ejecutarlos.
- Preparar un guion para un video de demostración.

Dime cuál prefieres y lo preparo.
