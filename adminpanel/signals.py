import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AdminNotification
from communications.email_utils import send_email
from django.conf import settings


@receiver(post_save, sender=AdminNotification)
def adminnotification_post_save(sender, instance, created, **kwargs):
    """Envía por correo la notificación administrativa a los administradores del sistema
    cuando se crea una AdminNotification. Esto hace que las notificaciones del panel
    también lleguen por email al equipo administrativo.
    """
    if not created:
        return
    try:
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        notif_link = f"{site_url}/adminpanel/notifications/{instance.id}/"
        context = {
            'title': instance.title,
            'message': instance.message,
            'notif_link': notif_link,
            'soporte_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
        }
        subject = f"Notificación del sistema: {instance.title}"

        # enviar a todos los registros que tengan rol de administrador del sistema
        from accounts.models import Registro
        admins = Registro.objects.filter(id_rol__nom_rol__in=['admin', 'administrator', 'administrador'])
        for a in admins:
            try:
                send_email(
                    subject=subject,
                    to_email=a.ema_usu,
                    template_html='email/admin_notification.html',
                    template_txt='email/admin_notification.txt',
                    context={**context, 'admin_name': f"{a.nom_usu} {a.ape_usu}"},
                    tipo='adminpanel_notification',
                    user=a,
                )
            except Exception:
                # no queremos que falle la creación de la notificación por un fallo en el email
                continue

        # además, si la notificación tiene asignado un usuario específico, enviarle también
        try:
            target = getattr(instance, 'user', None)
            if target and getattr(target, 'ema_usu', None):
                send_email(
                    subject=subject,
                    to_email=target.ema_usu,
                    template_html='email/admin_notification.html',
                    template_txt='email/admin_notification.txt',
                    context={**context, 'admin_name': f"{getattr(target,'nom_usu','')} {getattr(target,'ape_usu','')}"},
                    tipo='adminpanel_notification',
                    user=target,
                )
        except Exception:
            pass

        # enviar también a direcciones fijas configuradas via .env (coma-separadas)
        try:
            extra = getattr(settings, 'ADMIN_ALERT_EMAILS', None) or os.environ.get('ADMIN_ALERT_EMAILS')
            if extra:
                # puede ser lista separada por comas
                addrs = [e.strip() for e in extra.split(',') if e.strip()]
                for addr in addrs:
                    try:
                        send_email(
                            subject=subject,
                            to_email=addr,
                            template_html='email/admin_notification.html',
                            template_txt='email/admin_notification.txt',
                            context={**context, 'admin_name': addr},
                            tipo='adminpanel_notification',
                        )
                    except Exception:
                        continue
        except Exception:
            pass
    except Exception:
        # proteger el flujo principal de excepciones en el signal
        return
