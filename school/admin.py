from django.contrib import admin
from .models import Institucion, Curso, Matricula, Documento
from .models import MatriculaRequest
from django.utils import timezone
from django.core.mail import send_mail
import random
from .models import Matricula as MatriculaModel


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ('id_inst', 'nom_inst', 'id_adm')


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('id_cur', 'grd_cur', 'id_inst')


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('id_mat', 'fch_reg_mat', 'id_cur', 'id_est')


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('id_doc', 'id_mat')


@admin.register(MatriculaRequest)
class MatriculaRequestAdmin(admin.ModelAdmin):
    list_display = ('id_req', 'id_acu', 'id_est', 'id_inst', 'id_cur', 'estado', 'created_at')
    list_filter = ('estado', 'created_at')
    actions = ['accept_requests', 'reject_requests']

    def accept_requests(self, request, queryset):
        updated = 0
        for req in queryset.select_related('id_inst', 'id_est', 'id_acu'):
            if req.estado != 'pending':
                continue
            # if a specific course was provided, use it; otherwise pick a random course matching grado_solicitado
            curso = None
            if req.id_cur:
                curso = req.id_cur
            else:
                grado = req.grado_solicitado
                if grado:
                    candidates = list(Curso.objects.filter(id_inst=req.id_inst).filter(cup_disp_cur__gt=0))
                    # filter by numeric grade matching
                    candidates = [c for c in candidates if (str(grado) == ''.join(filter(str.isdigit, c.grd_cur)))]
                    if candidates:
                        curso = random.choice(candidates)
            if not curso:
                req.estado = 'rejected'
                req.obs = 'No hay cupos disponibles para el grado solicitado'
                req.save()
                continue

            # crear matrícula
            try:
                mat = MatriculaModel.objects.create(fch_reg_mat=timezone.now().date(), id_cur=curso, id_est=req.id_est, est_mat='activo')
                # decrementar cupo
                curso.cup_disp_cur = max(0, curso.cup_disp_cur - 1)
                curso.save()
                req.id_cur = curso
                req.estado = 'accepted'
                req.save()
                updated += 1
                # notificar al acudiente
                try:
                    if req.id_acu and req.id_acu.id_usu:
                        acudiente_reg = req.id_acu.id_usu
                        try:
                            from communications.email_utils import send_matricula_status_to_acudiente
                            send_matricula_status_to_acudiente(acudiente_reg, req, 'accepted', comment='', assigned_course=curso)
                        except Exception:
                            # fallback to send_mail
                            try:
                                if getattr(acudiente_reg, 'ema_usu', None):
                                    send_mail('Solicitud de matrícula aceptada', f'Tu solicitud ha sido aceptada. Curso asignado: {curso.grd_cur}.', 'no-reply@example.com', [acudiente_reg.ema_usu])
                            except Exception:
                                pass
                except Exception:
                    pass
            except Exception:
                req.estado = 'rejected'
                req.obs = 'Error al crear la matrícula'
                req.save()

        self.message_user(request, f'Aceptadas {updated} solicitud(es)')
    accept_requests.short_description = 'Aceptar solicitudes seleccionadas (asigna curso aleatorio)'

    def reject_requests(self, request, queryset):
        count = 0
        for req in queryset:
            if req.estado != 'pending':
                continue
            req.estado = 'rejected'
            req.obs = 'Rechazada por administrador'
            req.save()
            count += 1
        self.message_user(request, f'Rechazadas {count} solicitud(es)')
    reject_requests.short_description = 'Rechazar solicitudes seleccionadas'
