# Manual de Usuario — Roles y permisos

Este documento describe los roles disponibles en la aplicación, sus responsabilidades, los permisos habituales y las acciones que cada rol puede realizar en la interfaz. Está pensado para usuarios finales y personal administrativo que deben conocer qué funciones están a su alcance.

**Ubicación:** `docs/ROLES_USER_MANUAL.md`

**Audiencia:** personal administrativo, administradores del sistema, acudientes (padres/tutores), docentes y estudiantes.

---

**Resumen rápido:**
- El sistema distingue entre varios roles: **Administrador del sistema**, **Administrativo de institución**, **Docente**, **Acudiente (tutor)** y **Estudiante**. Cada rol tiene vistas y permisos diferentes; los administradores y administrativos tienen las capacidades de gestión más amplias.

---

## **Administrador del sistema**
- **Propósito:** gestionar la plataforma a nivel global, revisar logs, configurar alertas y manejar cuentas de alto nivel.
- **Permisos principales:**
  - Acceso completo al panel de Django Admin (`/admin/`).
  - Ver y gestionar `Registro` (usuarios), `EmailLog`, `AdminNotification`, `InstitucionRequest` y `CursoRequest`.
  - Configurar variables globales (vía `.env` o panel de configuración si existe), incluyendo `ADMIN_ALERT_EMAILS`.
  - Habilitar/deshabilitar cuentas y asignar roles.
  - Revisar y depurar envíos de correo (consultar `EmailLog` para ver `exito`/`error`).
- **Acciones frecuentes:**
  - Crear/editar cuentas administrativas.
  - Responder a incidentes reportados por administrativos o usuarios.
  - Revisar notificaciones del sistema y enviar comunicaciones.

**Cómo usar (pasos):**
  1. Iniciar sesión como superusuario en `/admin/`.
  2. Navegar a `EmailLog` para filtrar por fecha o destinatario y validar envíos.
  3. Actualizar `ADMIN_ALERT_EMAILS` en la configuración si es necesario (editar `.env` y reiniciar servicios en producción).

---

## **Administrativo de institución**
- **Propósito:** gestionar las solicitudes relacionadas con la institución y los cursos; manejar inscripciones y validar documentos.
- **Permisos principales:**
  - Acceso al panel administrativo propio (vistas dentro de la app `adminpanel`).
  - Revisar `InstitucionRequest` y `CursoRequest` y ejecutar acciones: **Aprobar**, **Solicitar información** o **Rechazar**.
  - Enviar notificaciones a remitentes y a administradores (las vistas llaman a helpers que envían correos y registran en `EmailLog`).
  - Crear cursos (individual o por lotes si el rol tiene permiso) y gestionar su estado.
- **Acciones frecuentes:**
  - Revisar lista de solicitudes pendientes y abrir cada detalle.
  - Completar campos de respuesta y usar los botones de la vista para aprobar o solicitar más información.
  - Tras la acción, el sistema envía correos automáticos y registra el envío en `EmailLog`.

**Cómo usar (pasos):**
  1. Entrar al panel `adminpanel` (vistas de gestión) con tu cuenta.
  2. Abrir `Solicitudes de institución` o `Solicitudes de curso`.
  3. Leer la solicitud, añadir comentarios si aplica y pulsar `Aprobar` / `Solicitar info` / `Rechazar`.

---

## **Docente**
- **Propósito:** gestionar contenidos y actividades asignadas a sus cursos; interactuar con estudiantes.
- **Permisos principales (típicos):**
  - Ver listados de cursos donde es docente.
  - Acceder a la lista de estudiantes matriculados en sus cursos.
  - Subir materiales o calificaciones (si la plataforma implementa estas funciones).
- **Acciones frecuentes:**
  - Consultar la lista de alumnos y su progreso.
  - Enviar comunicados a los estudiantes o acudientes (si la función está habilitada).

**Cómo usar (pasos):**
  1. Iniciar sesión con tu cuenta docente.
  2. Ir a la sección `Mis cursos` y seleccionar un curso.
  3. Revisar alumnos, subir recursos o publicar avisos.

---

## **Acudiente (padre/tutor)**
- **Propósito:** gestionar datos y documentación del estudiante a su cargo, recibir notificaciones y estado de matrícula.
- **Permisos principales:**
  - Ver la información del estudiante(s) asociado(s) (según la relación establecida en el sistema).
  - Subir documentos requeridos (identificación, autorizaciones, etc.).
  - Recibir correos de notificación sobre estado de matrícula, documentos o solicitudes.
- **Acciones frecuentes:**
  - Completar o actualizar el perfil del acudiente y del estudiante.
  - Subir documentos desde la interfaz `Mi cuenta` o `Documentos`.
  - Revisar la bandeja de notificaciones por correo y dentro del panel de usuario.

**Cómo usar (pasos):**
  1. Iniciar sesión desde la página principal.
  2. Ir a `Mi perfil` y confirmar datos de contacto (email/teléfono).
  3. Subir documentos en `Documentos` → `Agregar documento`.

---

## **Estudiante**
- **Propósito:** consultar información personal y académica, subir documentos y realizar procesos de matrícula si están habilitados.
- **Permisos principales:**
  - Actualizar perfil personal.
  - Subir documentos y ver el estado de su validación.
  - Consultar comunicaciones que le envíen (según el flujo del sistema).

**Cómo usar (pasos):**
  1. Entrar con tus credenciales.
  2. Ir a `Mi perfil` y `Documentos` para subir o revisar los archivos.

---

## **Permisos y anotaciones comunes**
- **Cambiar contraseña:** cualquier usuario puede cambiar su contraseña desde la opción de perfil o mediante el flujo de 'olvidé mi contraseña'.
- **Notificaciones por correo:** el sistema manda correos automáticos para eventos importantes (aprobación de solicitudes, peticiones de información, cambios de estado). Revisa `EmailLog` (administradores) para depurar envíos.
- **Registro de acciones:** acciones críticas (aprobaciones, rechazos) quedan registradas en el historial de la solicitud y pueden incluir comentarios y adjuntos.

---

## **Buenas prácticas por rol**
- **Administrador del sistema:** revisar `EmailLog` periódicamente, mantener .env y secrets seguros, limitar cuentas con permisos de superusuario.
- **Administrativo de institución:** adjuntar siempre observaciones claras al aprobar/rechazar; usar `Solicitar info` cuando la documentación no sea suficiente.
- **Acudiente / Estudiante:** mantener datos de contacto actualizados para no perder notificaciones.

---

## **Preguntas frecuentes (FAQ)**
- P: "No recibo correos" → R: revisar carpeta SPAM, confirmar email en `Mi perfil` y pedir al administrador que valide envíos en `EmailLog`.
- P: "No veo la opción de aprobar solicitudes" → R: probablemente tu cuenta no tiene rol `administrativo`; solicita al Administrador del sistema el permiso correspondiente.
- P: "Cómo veo quién envió una notificación" → R: en `AdminNotification` y en `EmailLog` aparece el remitente y el contenido resumido.

---

## **Contacto y soporte**
- Si tienes problemas con roles/permisos contacta al Administrador del sistema o al correo de soporte interno (definido por la organización).

---

Archivo creado: `docs/ROLES_USER_MANUAL.md`.
