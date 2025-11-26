# Manual de usuario — MatriSchool (versión local)

Este documento explica cómo instalar, configurar y usar la aplicación MatriSchool tal y como está en el repositorio. Incluye instrucciones rápidas para administradores, descripción de los flujos principales y cómo generar/ver los resultados de la evaluación usada en el proyecto.

**Ubicaciones importantes**
- Código raíz del proyecto: `.` (carpeta del workspace)
- Archivo de evaluación Excel: `EvaluacionSoftware_NombreProyecto_Versión.xlsx`
- Salidas de inspección y resultados: `outputs/` (contiene `eval_full_results.json`, `evaluacion_items_scores.csv`, `funcionalidad_missing_items.xlsx`)

**Resumen rápido**
- Estado actual: la aplicación tiene las funcionalidades principales implementadas (registro, paneles administrativos, peticiones de institución/curso, envío y registro de correos).

---

## 1. Requisitos
- Python 3.10+ (se probó con entornos virtuales). 
- Dependencias en `requirements.txt` o ambiente virtual del proyecto (`.venv`).
- Base de datos: SQLite por defecto en desarrollo; puede configurarse otras en `settings.py`.
- Acceso SMTP (opcional, para enviar correos); credenciales en el archivo `.env`.

## 2. Instalación rápida (Windows / PowerShell)
1. Abrir PowerShell en la carpeta del proyecto.
2. Activar venv (si existe):

```powershell
& .\.venv\Scripts\Activate.ps1
```

3. Instalar dependencias (si necesitas recrear el entorno):

```powershell
python -m pip install -r requirements.txt
```

4. Crear archivo `.env` con variables necesarias (ejemplo mínimo):

```
DJANGO_SECRET_KEY=tu_secreto
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu@mail
EMAIL_HOST_PASSWORD=contraseña
DEFAULT_FROM_EMAIL=MatriSchool <tu@mail>
```

5. Ejecutar migraciones y crear superusuario:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

6. Levantar servidor en desarrollo:

```powershell
python manage.py runserver
```

---

## 3. Configuración de correo (SMTP)
- Asegúrate de que las variables de `.env` estén cargadas por `settings.py`. El envío de correos usa `communications/email_utils.py` y registra cada intento en el modelo `EmailLog`.
- En producción es recomendable usar envío asíncrono (Celery / RQ) y no el envío sincrónico del servidor web.

## 4. Flujos principales (uso)

- Registro de usuario: el formulario de registro crea un `Registro`/`Usuario`.
- Matrícula: el flujo de matriculación guarda información y, al completarse, se pueden enviar notificaciones por correo.
- Subida de documentos: los estudiantes/usuarios pueden subir documentos; la subida dispara notificaciones y guarda registros asociados.
- Peticiones de institución/curso: un usuario puede solicitar creación/registro de institución o curso; estas peticiones son revisadas en el panel administrativo (`adminpanel`) y el personal administrativo puede aprobar/solicitar más información/rechazar.
- Notificaciones administrativas: al crear un `AdminNotification` se envían correos a administradores y se deja registro en `EmailLog` (esto está implementado vía señales en `adminpanel/signals.py`).

### Panel administrativo
- Accede con el superusuario a `/admin/` para ver modelos: `Registro`, `InstitucionRequest`, `CursoRequest`, `AdminNotification`, `EmailLog`.
- Las vistas del módulo `adminpanel` contienen botones para aprobar/rechazar y han sido actualizadas para enviar correos cuando se realizan acciones.

## 5. Interpretación y uso de `EmailLog`
- Cada envío usa la función central `send_email(subject, to_email, template_html, context, template_txt, tipo, user)` y guarda un registro en `EmailLog` con campos: `destinatario`, `asunto`, `cuerpo_resumen`, `exito`, `error`, `tipo`, `id_usu`, `fch_envio`.
- Para depurar correos, revisa el contenido de `EmailLog` en Django Admin o mediante consultas.

## 6. Evaluación de software (Excel)

Descripción: el repositorio incluye un Excel con hojas para distintas características (`FUNCIONALIDAD`, `FIABILIDAD`, `USABILIDAD`, etc.). El análisis automatizado produce archivos en `outputs/`.

- Archivos generados por el análisis automático:
  - `outputs/eval_full_results.json` — detalle de pesos, resultados por categoría y totales (conservative y provisional).
  - `outputs/evaluacion_items_scores.csv` — lista por item con la columna `pct` (porcentaje interpretado para cada ítem).
  - `outputs/funcionalidad_missing_items.xlsx` — exportación de ítems faltantes para `FUNCIONALIDAD`.

### Cómo ejecutar la rutina de evaluación (recomendado)
1. Activar el entorno virtual.  
2. Ejecutar un script Python (o el snippet usado por el equipo) que abra el Excel y genere los archivos mencionados. Si prefieres, puedo generar un script listo para ejecutar.

### Interpretación de resultados
- **Conservador:** trata celdas vacías como 0 → da una visión estricta (en nuestro análisis fue ~10.93%).
- **Provisional:** calcula sólo sobre los ítems evaluados y rescalea → da una visión parcial (en nuestro análisis fue 70.0% porque pocos ítems tenían respuestas).
- **Recomendación:** rellenar las celdas faltantes del Excel y volver a ejecutar la rutina para obtener un resultado definitivo.

## 7. Cómo completar la hoja de evaluación
- Para cada ítem completa la columna `VALOR` con uno de los formatos aceptados: número (p.ej. 0..100), puntaje (0..1 o 0..10) o texto `CUMPLE` / `NO CUMPLE`. El script interpreta estas opciones.
- Una vez rellenado, vuelve a ejecutar la rutina y revisa `outputs/eval_full_results.json`.

## 8. Comandos útiles

```powershell
# Activar entorno
& .\.venv\Scripts\Activate.ps1

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Levantar servidor
python manage.py runserver

# Ejecutar análisis manual (ejemplo en REPL o script)
python tools/run_eval.py   # (si se crea el script helper)
```

## 9. Checklist para release
- Verificar migraciones y backups.  
- Configurar variables de entorno y secretos.  
- Probar envíos de correo (en entorno staging).  
- Ejecutar pruebas automáticas y pruebas manuales de los flujos críticos (registro/matrícula/subida de documentos).  
- Asegurar que la evaluación Excel está completa antes de firmar una conformidad.

## 10. Añadidos y extensiones recomendadas
- Convertir los envíos de correo a asíncronos (Celery/RQ).  
- Añadir pruebas unitarias e integración para los endpoints críticos.  
- Documentar API y roles de usuarios en un `docs/` ampliado con capturas de pantalla.

---

Si quieres, ahora puedo:
- Generar una versión PDF del manual.
- Añadir capturas de pantalla y comandos exactos en `docs/`.
- Crear un script `tools/run_eval.py` que ejecute la rutina de evaluación automáticamente.

Archivo creado: `docs/USER_MANUAL.md`.
