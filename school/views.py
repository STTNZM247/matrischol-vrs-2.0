from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Institucion, Curso, MatriculaRequest, Documento, Matricula, Notificacion
from django.core.mail import send_mail
from people.models import Estudiante, Acudiente
from accounts.models import Registro
from django.db.models import Q
import datetime


@require_GET
def institutions_search(request):
    try:
        # Evitar redirecciones a login (que devuelven HTML). Para peticiones AJAX
        # comprobamos la autenticación manualmente y devolvemos JSON 401 cuando
        # no haya credenciales, de modo que el frontend pueda manejarlo.
        if not request.user.is_authenticated and not request.session.get('registro_id'):
            return JsonResponse({'results': [], 'error': 'No autenticado'}, status=401)

        q = request.GET.get('q', '').strip()
        if not q:
            return JsonResponse({'results': []})

        qs = Institucion.objects.filter(
            Q(nom_inst__icontains=q) |
            Q(tel_inst__icontains=q) |
            Q(ema_inst__icontains=q) |
            Q(dire_inst__icontains=q)
        )[:30]

        results = []
        for inst in qs:
            cursos = []
            for cur in inst.curso_set.all():
                cursos.append({
                    'id_cur': cur.id_cur,
                    'grd_cur': cur.grd_cur,
                    'cup_disp_cur': cur.cup_disp_cur,
                })
            results.append({
                'id_inst': inst.id_inst,
                'nom_inst': inst.nom_inst,
                'dire_inst': inst.dire_inst,
                'tel_inst': inst.tel_inst,
                'ema_inst': inst.ema_inst,
                'cursos': cursos,
            })

        return JsonResponse({'results': results})
    except Exception as e:
        try:
            import logging
            logging.exception('Error en institutions_search')
        except Exception:
            pass
        return JsonResponse({'results': [], 'error': 'Error interno', 'detail': str(e)}, status=500)


@require_POST
def matricula_request_create(request):
    # envolver toda la lógica en try/except para devolver siempre JSON legible al frontend
    try:
        # Si no hay autenticación, devolver JSON en vez de redirigir a login
        if not request.user.is_authenticated and not request.session.get('registro_id'):
            return JsonResponse({'status': 'error', 'error': 'No autenticado'}, status=401)
        # espera: POST form data: inst_id, cur_id, est_id
        inst_id = request.POST.get('inst_id')
        cur_id = request.POST.get('cur_id')
        est_id = request.POST.get('est_id')
        grado = request.POST.get('grado')

        if not (inst_id and est_id):
            return JsonResponse({'status': 'error', 'error': 'Faltan parámetros'}, status=400)

        # validar que el usuario sea el acudiente del estudiante o que sea el acudiente mismo
        acudiente = None
        reg = None
        # Intenta obtener el registro desde la sesión (forma usada en `accounts`)
        reg_id = request.session.get('registro_id')
        if reg_id:
            try:
                reg = Registro.objects.get(pk=reg_id)
            except Exception:
                reg = None

        # primero, buscar Acudiente vinculado al Registro si existe
        if reg:
            acudiente = Acudiente.objects.filter(id_usu=reg).first()

        # si no, intentar por request.user directamente
        if not acudiente:
            acudiente = Acudiente.objects.filter(id_usu=request.user).first()

        # Si todavía no hay acudiente, esperaremos a cargar el estudiante y usaremos su acudiente (si coincide con la sesión)
        est = get_object_or_404(Estudiante, pk=est_id)
        if not acudiente:
            if hasattr(est, 'id_acu') and est.id_acu:
                # si tenemos un registro en sesión, asegurarnos de que coincide
                if reg and getattr(est.id_acu, 'id_usu', None) != reg:
                    return JsonResponse({'status': 'error', 'error': 'No autorizado'}, status=403)
                acudiente = est.id_acu
            else:
                return JsonResponse({'status': 'error', 'error': 'No autorizado'}, status=403)

        # ahora validar que el estudiante pertenece al acudiente identificado
        if est.id_acu != acudiente:
            return JsonResponse({'status': 'error', 'error': 'El estudiante no pertenece al acudiente autenticado'}, status=403)

        inst = get_object_or_404(Institucion, pk=inst_id)

        # obtener curso solo si fue enviado (flujo antiguo); si no, trabajamos con grado
        db_cur = None
        if cur_id:
            try:
                db_cur = get_object_or_404(Curso, pk=cur_id)
            except Exception:
                return JsonResponse({'status': 'error', 'error': 'Curso no encontrado'}, status=404)
            if db_cur.id_inst != inst:
                return JsonResponse({'status': 'error', 'error': 'Curso no pertenece a la institución'}, status=400)

        # comprobar que el estudiante no tenga ya una matrícula activa
        if Matricula.objects.filter(id_est=est).exists():
            return JsonResponse({'status': 'error', 'error': 'El estudiante ya tiene matrícula asignada en otra institución'}, status=400)

        # Validación de documentos: combinar todos los Documento vinculados al estudiante
        # (por id_est y por la última matrícula) y verificar que entre todos están los campos requeridos.
        required_doc_fields = [
            'reg_civil_doc', 'doc_idn_acu', 'doc_idn_alum', 'cnt_vac_doc',
            'adres_doc', 'fot_alum_doc', 'cer_med_disca_doc', 'cer_esc_doc'
        ]

        # recolectar documentos relacionados
        try:
            docs_qs = Documento.objects.filter(id_est=est)
            last_mat = Matricula.objects.filter(id_est=est).order_by('-fch_reg_mat').first()
            if last_mat:
                docs_qs = docs_qs | Documento.objects.filter(id_mat=last_mat)
            docs = list(docs_qs)
        except Exception:
            docs = []

        missing = []
        for f in required_doc_fields:
            has = False
            # si alguno de los documentos tiene el campo, lo consideramos presente
            for d in docs:
                val = getattr(d, f, None)
                if val:
                    has = True
                    break
            # fallback: la foto del estudiante puede cubrir fot_alum_doc
            if f == 'fot_alum_doc' and est.foto_perfil:
                has = True
            # fallback adicional: aceptar la dirección escrita en el acudiente o en documento.adres_doc
            if f == 'adres_doc' and not has:
                try:
                    # si el acudiente tiene dir_acu configurada, la aceptamos como dirección
                    if getattr(est, 'id_acu', None) and getattr(est.id_acu, 'dir_acu', None):
                        has = True
                except Exception:
                    pass
            if not has:
                missing.append(f)

        if missing:
            return JsonResponse({'status': 'error', 'error': 'Faltan documentos del estudiante', 'missing': missing}, status=400)

        # si se envió curso explícito, comprobar cupo ahora
        if db_cur and db_cur.cup_disp_cur <= 0:
            return JsonResponse({'status': 'error', 'error': 'No hay cupos disponibles en el curso seleccionado'}, status=400)

        # crear solicitud: guardamos el grado solicitado (si fue enviado)
        expires = timezone.now() + datetime.timedelta(hours=24)
        grado_int = None
        try:
            if grado:
                grado_int = int(grado)
        except Exception:
            grado_int = None

        # evitar solicitudes duplicadas pendientes para el mismo estudiante e institución
        try:
            exists = MatriculaRequest.objects.filter(id_est=est, id_inst=inst, estado='pending').exists()
        except Exception:
            exists = False
        if exists:
            return JsonResponse({'status': 'error', 'error': 'Ya existe una solicitud pendiente para esta institución'}, status=400)

        req = MatriculaRequest.objects.create(
            id_acu=acudiente,
            id_est=est,
            id_inst=inst,
            id_cur=db_cur,
            grado_solicitado=grado_int,
            estado='pending',
            expires_at=expires,
        )

        # enviar confirmación al acudiente de que su solicitud fue recibida
        try:
            from communications.email_utils import send_matricula_request_received
            acudiente_reg = getattr(acudiente, 'id_usu', None) or getattr(acudiente, 'id_usu', None)
            if acudiente_reg:
                send_matricula_request_received(acudiente_reg, req)
        except Exception:
            pass

        # Notificar al administrativo de la institución (mail + notificación interna)
        try:
            admin = getattr(inst, 'id_adm', None)
            titulo = 'Nueva solicitud de matrícula'
            mensaje = f'Se ha recibido una nueva solicitud de matrícula para el estudiante {est.id_usu.nom_usu} {est.id_usu.ape_usu} (ID: {est.id_est}).'
            if grado_int:
                mensaje += f' Grado solicitado: {grado_int}.'
            if req.id_req:
                mensaje += f' ID solicitud: {req.id_req}.'

            # crear notificación en BD ligada al administrativo si existe
            if admin:
                try:
                    Notificacion.objects.create(id_admin=admin, id_req=req, titulo=titulo, mensaje=mensaje)
                except Exception:
                    pass

                # Además crear una AdminNotification para que aparezca en el panel de administrativos
                try:
                    admin_reg = getattr(admin, 'id_usu', None)
                    if admin_reg:
                        # importamos el modelo de notificaciones del adminpanel de forma diferida
                        from adminpanel.models import AdminNotification
                        try:
                            AdminNotification.objects.create(user=admin_reg, title=titulo, message=mensaje, matricula_request=req)
                        except Exception:
                            # evitar que falle el flujo principal si no se puede crear la notificación
                            pass
                except Exception:
                    pass

                # enviar email al administrativo si tiene correo asociado en su registro
                try:
                    adm_email = getattr(admin_reg, 'ema_usu', None) if admin_reg else None
                    if admin_reg and adm_email:
                        try:
                            from communications.email_utils import send_matricula_request_to_admin
                            send_matricula_request_to_admin(adm_reg, req)
                        except Exception:
                            # fallback: intentar con send_mail si algo falla
                            try:
                                send_mail(titulo, mensaje, 'no-reply@example.com', [adm_email])
                            except Exception:
                                pass
                except Exception:
                    pass

        except Exception:
            # no bloquear el flujo por fallos en notificación
            pass

        return JsonResponse({'status': 'ok', 'request_id': req.id_req})
    except Exception as e:
        # Capturar cualquier error inesperado y devolver JSON legible al frontend
        try:
            import logging
            logging.exception('Error creando MatriculaRequest')
        except Exception:
            pass
        return JsonResponse({'status': 'error', 'error': 'Error interno al procesar la solicitud', 'detail': str(e)}, status=500)
