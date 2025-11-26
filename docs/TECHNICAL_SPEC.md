# Especificaciones Técnicas — MatriSchool

Este documento técnico describe la instalación, configuración, ejecución en desarrollo y despliegue en producción de la aplicación MatriSchool. Incluye recomendaciones operativas, despliegue con Docker/Gunicorn+Nginx, uso de correo, tareas asíncronas y checklist de producción.

**Audiencia:** administradores de infraestructura, devops y desarrolladores encargados de puesta en producción.

---

## Contenido
- Requisitos
- Instalación en entorno de desarrollo
- Variables de entorno y configuración
- Base de datos y migraciones
- Archivos estáticos y media
- Correo (SMTP)
- Tareas asíncronas (recomendado)
- Logs, monitoring y backups
- Despliegue en producción (Gunicorn + Nginx)
- Despliegue con Docker / docker-compose
- Integración continua (CI/CD) y checklist de release
- Ejemplos de comandos (PowerShell y Bash)
- Troubleshooting y notas finales

---

## Requisitos
- Python 3.10+ (recomendado 3.10-3.11)
- pip
- virtualenv / venv
- PostgreSQL (recomendado en producción) o MySQL/otra RDBMS soportada por Django
- Redis (si se usa Celery)
- Nginx (proxy reverso) y Gunicorn para servir la app en producción
- Certbot / Let's Encrypt para certificados SSL
- Sistema operativo: Ubuntu 20.04+/Debian 11+ (o Windows para desarrollo)

---

## Instalación en desarrollo
1. Clonar el repositorio y situarse en la carpeta raíz del proyecto.
2. Crear y activar un entorno virtual:

PowerShell (Windows):
```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```

Bash (Linux/macOS):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Crear `.env` con variables mínimas (ejemplo):
```
DJANGO_SECRET_KEY=REEMPLAZAR
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=mi@correo
EMAIL_HOST_PASSWORD=secreto
DEFAULT_FROM_EMAIL="MatriSchool <mi@correo>"
```

5. Migraciones y superusuario:
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. Ejecutar servidor en desarrollo:
```bash
python manage.py runserver
```

---

## Variables de entorno y configuración (relevantes)
- `DJANGO_SECRET_KEY` — secreto Django.
- `DEBUG` — True/False.
- `DATABASE_URL` — URL de conexión (ej. `postgres://user:pass@host:5432/dbname`).
- `ALLOWED_HOSTS` — hosts permitidos en producción.
- Email: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- `ADMIN_ALERT_EMAILS` — lista de emails separados por comas para recibir alertas administrativas.
- `REDIS_URL` — si se usa Redis para Celery.
- `SENTRY_DSN` — si se integra con Sentry para errores.

Notes: cargar `.env` en `settings.py` usando python-dotenv o un loader manual; nunca commitear `.env` ni credenciales.

---

## Base de datos y migraciones
- En desarrollo SQLite es suficiente; en producción usar PostgreSQL.
- Comandos:
```bash
python manage.py makemigrations
python manage.py migrate
```
- Backup (Postgres):
```bash
pg_dump -Fc -U usuario -h host dbname > backup_$(date +%F).dump
```
- Restauración:
```bash
pg_restore -U usuario -h host -d dbname backup.dump
```

---

## Archivos estáticos y media
- Configurar `STATIC_ROOT` y `MEDIA_ROOT` en `settings.py`.
- Antes del deploy ejecutar:
```bash
python manage.py collectstatic --noinput
```
- Servir archivos estáticos con Nginx en producción.

---

## Correo (SMTP)
- La aplicación usa `communications/email_utils.py` para enviar correos y guarda envíos en `EmailLog`.
- En producción usar credenciales de un proveedor (SendGrid, SES, SMTP con cuenta dedicada).
- Recomendación: probar SMTP en staging con credenciales válidas; no usar cuentas personales en producción.

---

## Tareas asíncronas (recomendado)
- En producción los envíos de correo y tareas pesadas deben ejecutarse de forma asíncrona. Recomendación:
  - Backend: Celery
  - Broker: Redis o RabbitMQ
  - Worker: Celery worker, supervisado por systemd o process manager

Ejemplo mínimo de comandos para Celery:
```bash
# Iniciar worker
celery -A <project_name> worker --loglevel=info
# Iniciar beat si hay tareas periódicas
celery -A <project_name> beat --loglevel=info
```

Nota: integrar tasks que llamen a `communications.email_utils.send_email` desde tareas Celery.

---

## Logs, monitoring y backups
- Logging: configurar `LOGGING` en `settings.py` para enviar errores a Sentry y logs a fichero.
- Monitoring: integrar métricas (Prometheus + Grafana) si se requiere.
- Backups: programar dumps de BD y snapshots de media en almacenamiento seguro (S3 o disco montado), conservar al menos 7 días.

---

## Despliegue en producción (Gunicorn + Nginx)
1. Crear entorno virtual y desplegar el código.
2. Instalar dependencias y ejecutar migraciones.
3. Ejecutar `collectstatic`.
4. Configurar Gunicorn systemd unit.

Ejemplo `gunicorn.service` (Ubuntu/systemd):
```
[Unit]
Description=gunicorn daemon for matrischol
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/matrischol
EnvironmentFile=/srv/matrischol/.env
ExecStart=/srv/matrischol/.venv/bin/gunicorn --workers 3 --bind unix:/srv/matrischol/matrischol.sock matrischol_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

Ejemplo de bloque Nginx (sitio):
```
server {
    listen 80;
    server_name ejemplo.com www.ejemplo.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /srv/matrischol;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/srv/matrischol/matrischol.sock;
    }
}
```

Habilitar SSL con Certbot:
```bash
sudo certbot --nginx -d ejemplo.com -d www.ejemplo.com
```

---

## Despliegue con Docker (opción alternativa)
- Ventajas: reproducibilidad y facilidad para CI/CD.
- Proponer `Dockerfile` base y `docker-compose.yml` con servicios: web (gunicorn), db (postgres), redis (opcional), nginx (opcional), worker (celery).

Ejemplo `Dockerfile` (resumido):
```
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["gunicorn", "matrischol_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Ejemplo `docker-compose.yml` (resumido):
```yaml
version: '3.8'
services:
  db:
    image: postgres:14
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: matrischol
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  redis:
    image: redis:7

  web:
    build: .
    command: gunicorn matrischol_project.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A matrischol_project worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - redis
      - db

volumes:
  db_data:
```

Notas: ajustar recursos (workers) según CPU/memoria; no exponer servicios de DB/Redis a internet.

---

## CI/CD sugerido
- Pipeline (ejemplo GitHub Actions / GitLab CI):
  - Steps: checkout → setup Python → install deps → run linters → run tests → build image → push image → desplegar en staging → ejecutar migraciones → smoke tests → promocionar a producción.
- Ejecutar migraciones desde CI/CD con cuidado: usar `--check` en staging y manual para producción o ejecutar migraciones automatizadas con aprobación.

---

## Checklist de producción (previo a release)
 - [ ] Revisar `DEBUG=False` y `ALLOWED_HOSTS` configurados.
 - [ ] Secretos y credenciales en gestor seguro (Vault, secretos del proveedor).
 - [ ] SSL configurado y renovaciones automáticas.
 - [ ] Backups programados para BD y media.
 - [ ] Pruebas automáticas y smoke tests satisfactorios.
 - [ ] Monitorización activa y alertas configuradas.
 - [ ] Tareas asíncronas funcionando (Celery workers conectados).
 - [ ] Revisión de logs y pruebas manuales de flujos críticos (registro, matrícula, subida de documentos, notificaciones por correo).

---

## Comandos rápidos (PowerShell)
```powershell
& .\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
# En producción con gunicorn
.\.venv\Scripts\gunicorn matrischol_project.wsgi:application --bind 0.0.0.0:8000
```

## Comandos rápidos (Bash)
```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
# gunicorn
.venv/bin/gunicorn matrischol_project.wsgi:application --bind unix:/srv/matrischol/matrischol.sock
```

---

## Run Eval (rutina de evaluación Excel)
- Se recomienda añadir `tools/run_eval.py` para ejecutar automáticamente la lectura y producción de `outputs/`.
- El script debe aceptar `--input`, `--outdir`, `--treat-empty-as-zero` y `--mapping-file`.

---

## Troubleshooting (problemas comunes)
- Problema: correos no se envían → comprobar credenciales SMTP y `EMAIL_BACKEND` en `settings.py`; revisar `EmailLog`.
- Problema: staticfiles 404 → verificar `collectstatic` y rutas en Nginx.
- Problema: error de migraciones → correr `makemigrations` y revisar cambios de modelos; probar en staging.

---

## Notas finales
- Este documento cubre las necesidades técnicas para pasar de desarrollo a producción. Puedo generar plantillas adicionales (systemd unit files, `docker-compose.prod.yml`, scripts de backup y `tools/run_eval.py`) si decides que implementemos despliegue con Docker o con systemd.
