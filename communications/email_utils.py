from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import EmailLog
from django.utils import timezone


def send_email(subject: str, to_email: str, template_html: str, context: dict, template_txt: str = None, tipo: str = 'generic', user=None):
    """Envía un email HTML + texto y registra resultado en EmailLog.
    :param subject: Asunto del correo
    :param to_email: Destinatario
    :param template_html: Ruta template HTML
    :param context: Contexto para render
    :param template_txt: Ruta template texto plano (opcional)
    :param tipo: Clasificación (password_change, notification, etc.)
    :param user: Registro relacionado (opcional)
    """
    # Agregar datos comunes (logo, fecha actual) antes de renderizar
    if 'now' not in context:
        context['now'] = timezone.now()
    # Logo global configurable en settings.SITE_LOGO_URL (opcional)
    global_logo = getattr(settings, 'SITE_LOGO_URL', None)
    if 'logo_url' not in context and global_logo:
        context['logo_url'] = global_logo
    html_content = render_to_string(template_html, context)
    if template_txt:
        text_content = render_to_string(template_txt, context)
    else:
        # Fallback básico quitando tags simples
        text_content = html_content.replace('<br>', '\n').replace('<br/>', '\n').replace('</p>', '\n').replace('<p>', '').replace('<strong>', '').replace('</strong>', '')

    # Envío por SendGrid API
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    sg_api_key = os.getenv("EMAIL_HOST_PASSWORD") or getattr(settings, "EMAIL_HOST_PASSWORD", None)
    from_email = settings.DEFAULT_FROM_EMAIL
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=text_content,
        html_content=html_content
    )

    log = EmailLog(
        destinatario=to_email,
        asunto=subject,
        cuerpo_resumen=text_content[:240],
        tipo=tipo,
        id_usu=user,
    )
    try:
        sg = SendGridAPIClient(sg_api_key)
        response = sg.send(message)
        log.exito = response.status_code in [200, 202]
        log.error = None if log.exito else f"SendGrid error: {response.status_code} {response.body}"
    except Exception as e:
        log.exito = False
        log.error = str(e)
    log.save()
    return log


def send_password_change_email(registro, ip=None, ua=None):
    """Email específico para cambio de contraseña."""
    context = {
        'nombre': f"{registro.nom_usu} {registro.ape_usu}",
        'fecha': timezone.now(),
        'ip': ip or 'desconocida',
        'ua': ua or 'desconocido',
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject='Tu contraseña ha sido cambiada',
        to_email=registro.ema_usu,
        template_html='email/password_changed.html',
        template_txt='email/password_changed.txt',
        context=context,
        tipo='password_change',
        user=registro,
    )


def send_password_reset_email(registro, token):
    from django.conf import settings
    reset_link = f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/accounts/reset/{token}/"
    context = {
        'nombre': f"{registro.nom_usu} {registro.ape_usu}",
        'reset_link': reset_link,
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject='Instrucciones para restablecer tu contraseña',
        to_email=registro.ema_usu,
        template_html='email/password_reset.html',
        template_txt='email/password_reset.txt',
        context=context,
        tipo='password_reset',
        user=registro,
    )


def send_student_registration_email(acudiente_registro, estudiante_nombre_completo, estudiante_num_doc):
    """Email de confirmación al acudiente tras registrar un estudiante.
    :param acudiente_registro: Objeto Registro del acudiente
    :param estudiante_nombre_completo: Nombre completo del estudiante registrado
    :param estudiante_num_doc: Número de documento del estudiante
    """
    from django.conf import settings
    panel_url = f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/accounts/panel/acudiente/"
    context = {
        'acudiente_nombre': f"{acudiente_registro.nom_usu} {acudiente_registro.ape_usu}",
        'estudiante_nombre': estudiante_nombre_completo,
        'estudiante_doc': estudiante_num_doc,
        'panel_url': panel_url,
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject='¡Felicidades! Estudiante registrado exitosamente',
        to_email=acudiente_registro.ema_usu,
        template_html='email/student_registered.html',
        template_txt='email/student_registered.txt',
        context=context,
        tipo='student_registration',
        user=acudiente_registro,
    )


def send_documents_uploaded_email(acudiente_registro, estudiante_nombre_completo, uploaded_fields=None):
    """Notifica al acudiente que los documentos fueron subidos correctamente.
    :param acudiente_registro: objeto Registro del acudiente
    :param estudiante_nombre_completo: nombre completo del estudiante
    :param uploaded_fields: lista de campos subidos (opcional)
    """
    from django.conf import settings
    panel_url = f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/accounts/panel/acudiente/"
    context = {
        'acudiente_nombre': f"{acudiente_registro.nom_usu} {acudiente_registro.ape_usu}",
        'estudiante_nombre': estudiante_nombre_completo,
        'uploaded_fields': uploaded_fields or [],
        'panel_url': panel_url,
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject='Documentos subidos correctamente',
        to_email=acudiente_registro.ema_usu,
        template_html='email/documents_uploaded.html',
        template_txt='email/documents_uploaded.txt',
        context=context,
        tipo='documents_uploaded',
        user=acudiente_registro,
    )


def send_matricula_request_to_admin(admin_registro, req):
    """Notifica por email al administrativo que recibe una nueva solicitud de matrícula."""
    from django.conf import settings
    estudiante_nombre = f"{req.id_est.id_usu.nom_usu} {req.id_est.id_usu.ape_usu}" if getattr(req, 'id_est', None) and getattr(req.id_est, 'id_usu', None) else 'Estudiante'
    context = {
        'admin_name': f"{getattr(admin_registro, 'nom_usu', '')} {getattr(admin_registro, 'ape_usu', '')}",
        'estudiante_nombre': estudiante_nombre,
        'institucion': getattr(req.id_inst, 'nom_inst', ''),
        'grado_solicitado': getattr(req, 'grado_solicitado', None),
        'request_id': getattr(req, 'id_req', None),
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject='Nueva solicitud de matrícula recibida',
        to_email=getattr(admin_registro, 'ema_usu', None),
        template_html='email/matricula_request_admin.html',
        template_txt='email/matricula_request_admin.txt',
        context=context,
        tipo='matricula_request_admin',
        user=admin_registro,
    )


def send_matricula_status_to_acudiente(acudiente_registro, req, status, comment=None, assigned_course=None):
    """Notifica al acudiente cuando el administrador cambia el estado de la solicitud.
    :param status: 'accepted'|'rejected'|'pending'
    :param assigned_course: Curso object or None
    """
    from django.conf import settings
    estudiante_nombre = f"{req.id_est.id_usu.nom_usu} {req.id_est.id_usu.ape_usu}" if getattr(req, 'id_est', None) and getattr(req.id_est, 'id_usu', None) else 'el estudiante'
    course_label = getattr(assigned_course, 'grd_cur', None) if assigned_course else None
    context = {
        'acudiente_nombre': f"{acudiente_registro.nom_usu} {acudiente_registro.ape_usu}",
        'estudiante_nombre': estudiante_nombre,
        'status': status,
        'comment': comment or '',
        'assigned_course': course_label,
        'panel_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/accounts/panel/acudiente/",
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    subject_map = {
        'accepted': 'Solicitud de matrícula aceptada',
        'rejected': 'Solicitud de matrícula rechazada',
        'pending': 'Solicitud de matrícula en espera',
    }
    subject = subject_map.get(status, 'Actualización de su solicitud de matrícula')
    return send_email(
        subject=subject,
        to_email=getattr(acudiente_registro, 'ema_usu', None),
        template_html='email/matricula_request_status_acudiente.html',
        template_txt='email/matricula_request_status_acudiente.txt',
        context=context,
        tipo='matricula_status',
        user=acudiente_registro,
    )


def send_matricula_request_received(acudiente_registro, req):
    """Confirma al acudiente que su solicitud fue recibida y que recibirá actualizaciones."""
    from django.conf import settings
    estudiante_nombre = f"{req.id_est.id_usu.nom_usu} {req.id_est.id_usu.ape_usu}" if getattr(req, 'id_est', None) and getattr(req.id_est, 'id_usu', None) else 'el estudiante'
    context = {
        'acudiente_nombre': f"{acudiente_registro.nom_usu} {acudiente_registro.ape_usu}",
        'estudiante_nombre': estudiante_nombre,
        'institucion': getattr(req.id_inst, 'nom_inst', ''),
        'request_id': getattr(req, 'id_req', None),
        'panel_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/accounts/panel/acudiente/",
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject='Hemos recibido tu solicitud de matrícula',
        to_email=getattr(acudiente_registro, 'ema_usu', None),
        template_html='email/matricula_request_received.html',
        template_txt='email/matricula_request_received.txt',
        context=context,
        tipo='matricula_received',
        user=acudiente_registro,
    )


def send_institucion_status_email(admin_registro, req, status, comments=None):
    """Notifica al administrativo de la institución cuando su solicitud cambia de estado.
    :param admin_registro: objeto Registro del administrativo (req.id_adm.id_usu)
    :param req: objeto InstitucionRequest
    :param status: uno de 'approved'|'rejected'|'needs_info'
    :param comments: comentarios del revisor
    """
    from django.conf import settings
    status_map = {
        'approved': 'aprobada',
        'rejected': 'rechazada',
        'needs_info': 'requiere información',
    }
    subject_status = status_map.get(status, 'actualizada')
    subject = f'Solicitud de institución {subject_status}: {getattr(req, "nom_inst", "")}'
    context = {
        'admin_name': f"{getattr(admin_registro, 'nom_usu', '')} {getattr(admin_registro, 'ape_usu', '')}",
        'institucion_nombre': getattr(req, 'nom_inst', ''),
        'request_id': getattr(req, 'id_req', None),
        'status': status,
        'status_label': subject_status,
        'comments': comments or '',
        'panel_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/adminpanel/administracion_institucion_requests/",
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject=subject,
        to_email=getattr(admin_registro, 'ema_usu', None),
        template_html='email/institucion_request_status_administrativo.html',
        template_txt='email/institucion_request_status_administrativo.txt',
        context=context,
        tipo='institucion_request_status',
        user=admin_registro,
    )


def send_curso_request_admin(admin_registro, req):
    """Notifica por email a un administrador del sistema cuando se crea una solicitud de cursos."""
    from django.conf import settings
    estudiante_nombre = f"{getattr(req.submitted_by, 'nom_usu', '')} {getattr(req.submitted_by, 'ape_usu', '')}" if getattr(req, 'submitted_by', None) else ''
    context = {
        'admin_name': f"{getattr(admin_registro, 'nom_usu', '')} {getattr(admin_registro, 'ape_usu', '')}",
        'institucion': getattr(req.id_inst, 'nom_inst', ''),
        'mode': getattr(req, 'mode', ''),
        'start_grade': getattr(req, 'start_grade', None),
        'end_grade': getattr(req, 'end_grade', None),
        'sections': getattr(req, 'sections', None),
        'cupos': getattr(req, 'cupos', None),
        'estudiante_nombre': estudiante_nombre,
        'request_id': getattr(req, 'id_req', None),
        'panel_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/adminpanel/administracion_curso_requests/",
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    return send_email(
        subject=f'Nueva solicitud de cursos en {context.get("institucion")}',
        to_email=getattr(admin_registro, 'ema_usu', None),
        template_html='email/curso_request_admin.html',
        template_txt='email/curso_request_admin.txt',
        context=context,
        tipo='curso_request_admin',
        user=admin_registro,
    )


def send_curso_status_to_submitter(submitter_registro, req, status, comments=None):
    """Notifica al solicitante de cursos cuando su solicitud cambia de estado."""
    from django.conf import settings
    status_map = {
        'approved': 'aprobada',
        'rejected': 'rechazada',
        'needs_info': 'requiere información',
    }
    subject_status = status_map.get(status, 'actualizada')
    context = {
        'submitter_name': f"{getattr(submitter_registro, 'nom_usu', '')} {getattr(submitter_registro, 'ape_usu', '')}",
        'institucion': getattr(req.id_inst, 'nom_inst', ''),
        'request_id': getattr(req, 'id_req', None),
        'status': status,
        'status_label': subject_status,
        'comments': comments or '',
        'panel_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/accounts/panel/acudiente/",
        'soporte_email': settings.DEFAULT_FROM_EMAIL,
    }
    subject = f'Solicitud de cursos {subject_status} para {context.get("institucion")}'
    return send_email(
        subject=subject,
        to_email=getattr(submitter_registro, 'ema_usu', None),
        template_html='email/curso_request_status_submitter.html',
        template_txt='email/curso_request_status_submitter.txt',
        context=context,
        tipo='curso_request_status',
        user=submitter_registro,
    )
