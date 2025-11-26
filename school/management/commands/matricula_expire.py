from django.core.management.base import BaseCommand
from school.models import MatriculaRequest
from django.utils import timezone
from django.core.mail import send_mail

class Command(BaseCommand):
    help = 'Expira solicitudes de matrícula pendientes tras 24 horas'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = MatriculaRequest.objects.filter(estado='pending', expires_at__lt=now)
        count = 0
        for req in expired:
            req.estado = 'rejected'
            req.obs = 'Expirada automáticamente tras 24h sin respuesta'
            req.save()
            count += 1
            # TODO: notificar al acudiente por email/in-app
            try:
                if req.id_acu and req.id_acu.id_usu and req.id_acu.id_usu.ema_usu:
                    send_mail('Solicitud de matrícula rechazada', 'Tu solicitud fue rechazada automáticamente por no recibir respuesta en 24h.', 'no-reply@example.com', [req.id_acu.id_usu.ema_usu])
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f'Procesadas {count} solicitudes expirada(s)'))
