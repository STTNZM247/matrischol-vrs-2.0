# Manual Técnico — MatriSchol

Este manual describe la instalación, configuración, despliegue y mantenimiento de la plataforma MatriSchol. Está pensado para desarrolladores y administradores.

---

## 1. Requisitos
- Python 3.10+
- pip
- virtualenv o venv
- PostgreSQL (producción) o SQLite (desarrollo)
- Cuenta en Cloudinary (media) y SendGrid (correo)
- Render.com o servidor propio para despliegue

---

## 2. Instalación y Configuración
### 2.1. Clonar y preparar entorno
```powershell
# Clona el repositorio y entra a la carpeta
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2.2. Variables de entorno (`.env`)
Ejemplo mínimo:
```
DJANGO_SECRET_KEY=tu_secreto
DEBUG=True
SITE_URL=https://matrischol.onrender.com
CLOUDINARY_CLOUD_NAME=xxxx
CLOUDINARY_API_KEY=xxxx
CLOUDINARY_API_SECRET=xxxx
SENDGRID_API_KEY=xxxx
DEFAULT_FROM_EMAIL=MatriSchol <tu@mail>
```

### 2.3. Migraciones y superusuario
```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 2.4. Archivos estáticos y media
- Ejecuta: `python manage.py collectstatic --noinput`
- Los archivos media se guardan en Cloudinary automáticamente.

---

## 3. Servicios Externos
### 3.1. Cloudinary (media)
- Configura las variables `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
- Los archivos subidos se almacenan en la nube y no se pierden al reiniciar el servidor.

### 3.2. SendGrid (correo)
- Configura `SENDGRID_API_KEY` y `DEFAULT_FROM_EMAIL`.
- El sistema usa la API de SendGrid para enviar notificaciones y recuperación de contraseña.

---

## 4. Despliegue en Render
- Sube el código a GitHub y conecta el repo en Render.com.
- Define las variables de entorno en el dashboard de Render.
- Render ejecuta automáticamente migraciones y el servidor.

---

## 5. Estructura del Proyecto
- `accounts/`: gestión de usuarios, autenticación, recuperación de contraseña.
- `school/`: modelos y vistas de matrículas, cursos, instituciones.
- `adminpanel/`: panel administrativo y notificaciones.
- `communications/`: utilidades de correo y logs de envíos.
- `media/`: (solo en local) — en producción, todo va a Cloudinary.
- `outputs/`: reportes y archivos de evaluación.
- `docs/`: manuales y documentación.

---

## 6. Buenas Prácticas y Mantenimiento
- Haz backup regular de la base de datos.
- No subas archivos `.env` ni credenciales al repositorio.
- Usa cuentas de correo y Cloudinary dedicadas para producción.
- Revisa los logs de errores y de correo (`EmailLog` en admin).
- Actualiza dependencias con regularidad.

---

## 7. Troubleshooting
- **No se envían correos:** revisa `SENDGRID_API_KEY` y logs en `EmailLog`.
- **No se guardan imágenes:** revisa las variables de Cloudinary y la configuración en `settings.py`.
- **Error en migraciones:** ejecuta `python manage.py makemigrations` y `python manage.py migrate`.
- **Problemas de acceso:** revisa `ALLOWED_HOSTS` y la variable `SITE_URL`.

---

¿Dudas técnicas? Consulta este manual o contacta al equipo de desarrollo.
