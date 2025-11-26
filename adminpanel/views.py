from django.shortcuts import render, redirect
import logging
from django.urls import reverse
from django.contrib import messages
from accounts.models import Registro
from accounts.models import Rol
from .forms import RegistroCreateForm, RegistroEditForm, PasswordChangeForm
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.db.utils import OperationalError
from school.models import Institucion, Curso
from people.models import Maestro
from django.db.models import Count
from django.db import IntegrityError
from accounts.models import Administrativo as AdministrativoModel
from django.http import HttpResponse
import csv

# import audit model lazily to avoid circular issues
from .models import AdminActionLog
from .models import InstitucionRequest, AdminNotification
from .forms import InstitucionRequestForm
from .models import CursoRequest
from .forms import CursoRequestForm
from school.models import MatriculaRequest, Matricula
from django.utils import timezone
from school.models import Documento
from django.conf import settings
import random
from school.models import Asignatura, Horario
from django import forms
from communications.email_utils import send_institucion_status_email
from communications.email_utils import send_curso_request_admin, send_curso_status_to_submitter


def log_action(request, action, model_name, object_repr='', details=''):
    try:
        reg = None
        reg_id = request.session.get('registro_id')
        if reg_id:
            reg = Registro.objects.filter(pk=reg_id).first()
        AdminActionLog.objects.create(user=reg, action=action, model_name=model_name, object_repr=str(object_repr)[:200], details=details)
    except Exception:
        # avoid crashing admin on logging errors
        pass


def admin_required(view_func):
    def _wrapped(request, *args, **kwargs):
        reg_id = request.session.get('registro_id')
        if not reg_id:
            return redirect('accounts:login')
        try:
            reg = Registro.objects.get(pk=reg_id)
        except Registro.DoesNotExist:
            return redirect('accounts:login')
        rol_name = (reg.id_rol.nom_rol or '').lower() if reg.id_rol else ''
        # Accept only explicit admin role names in English and Spanish.
        # Avoid substring matches like 'administrativo' which are not global admins.
        is_admin_role = rol_name in ('admin', 'administrator', 'administrador')
        if not is_admin_role:
            messages.error(request, 'No tienes permiso para acceder al panel de administración')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


@admin_required
def dashboard_view(request):
    # Basic dashboard placeholders — we'll expand with metrics later
    stats = {
        'total_usuarios': Registro.objects.count(),
        'total_roles': Rol.objects.count(),
    }
    return render(request, 'adminpanel/dashboard.html', {'stats': stats})


@admin_required
def registro_list(request):
    q = request.GET.get('q', '').strip()
    qs = Registro.objects.all().order_by('id_usu')
    if q:
        qs = qs.filter(Q(nom_usu__icontains=q) | Q(ape_usu__icontains=q) | Q(ema_usu__icontains=q))
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    registros = paginator.get_page(page)
    return render(request, 'adminpanel/registro_list.html', {'registros': registros, 'q': q})


@admin_required
def rol_list(request):
    q = request.GET.get('q', '').strip()
    qs = Rol.objects.all().order_by('id_rol')
    if q:
        qs = qs.filter(nom_rol__icontains=q)
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    roles = paginator.get_page(page)
    return render(request, 'adminpanel/rol_list.html', {'roles': roles, 'q': q})


@admin_required
def rol_create(request):
    if request.method == 'POST':
        from .forms import RolForm
        form = RolForm(request.POST)
        if form.is_valid():
            rol = form.save()
            log_action(request, 'create', 'Rol', object_repr=rol.nom_rol)
            messages.success(request, 'Rol creado correctamente')
            return redirect('adminpanel:rol_list')
    else:
        from .forms import RolForm
        form = RolForm()
    return render(request, 'adminpanel/rol_form.html', {'form': form, 'create': True})


@admin_required
def rol_edit(request, pk):
    try:
        rol = Rol.objects.get(pk=pk)
    except Rol.DoesNotExist:
        messages.error(request, 'Rol no encontrado')
        return redirect('adminpanel:rol_list')
    from .forms import RolForm
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            log_action(request, 'update', 'Rol', object_repr=rol.nom_rol)
            messages.success(request, 'Rol actualizado')
            return redirect('adminpanel:rol_list')
    else:
        form = RolForm(instance=rol)
    return render(request, 'adminpanel/rol_form.html', {'form': form, 'create': False, 'rol': rol})


@admin_required
def rol_delete(request, pk):
    try:
        rol = Rol.objects.get(pk=pk)
    except Rol.DoesNotExist:
        messages.error(request, 'Rol no encontrado')
        return redirect('adminpanel:rol_list')
    if request.method == 'POST':
        name = rol.nom_rol
        rol.delete()
        log_action(request, 'delete', 'Rol', object_repr=name)
        messages.success(request, 'Rol eliminado')
        return redirect('adminpanel:rol_list')
    return render(request, 'adminpanel/rol_confirm_delete.html', {'rol': rol})


@admin_required
def registro_create(request):
    from .forms import AdminRegistroCreateForm
    if request.method == 'POST':
        form = AdminRegistroCreateForm(request.POST, request.FILES)
        if form.is_valid():
            reg = form.save(commit=True, files=request.FILES)
            log_action(request, 'create', 'Registro', object_repr=f"{reg.nom_usu} {reg.ape_usu}")
            messages.success(request, 'Registro creado correctamente')
            return redirect('adminpanel:registro_list')
    else:
        form = AdminRegistroCreateForm()
    return render(request, 'adminpanel/registro_form.html', {'form': form, 'create': True})


@admin_required
def registro_edit(request, pk):
    try:
        reg = Registro.objects.get(pk=pk)
    except Registro.DoesNotExist:
        messages.error(request, 'Registro no encontrado')
        return redirect('adminpanel:registro_list')
    from .forms import AdminRegistroCreateForm
    # try to get existing administrativo to populate admin fields
    from accounts.models import Administrativo as AdmModel
    adm = AdmModel.objects.filter(id_usu=reg).first()

    if request.method == 'POST':
        form = AdminRegistroCreateForm(request.POST, request.FILES, instance=reg)
        if form.is_valid():
            reg = form.save(commit=True, files=request.FILES)
            log_action(request, 'update', 'Registro', object_repr=f"{reg.nom_usu} {reg.ape_usu}")
            messages.success(request, 'Registro actualizado')
            return redirect('adminpanel:registro_list')
    else:
        initial = {}
        if adm:
            initial = {
                'num_doc_adm': adm.num_doc_adm,
                'tel_adm': adm.tel_adm,
                'dir_adm': adm.dir_adm,
                'tip_carg_adm': adm.tip_carg_adm,
            }
        form = AdminRegistroCreateForm(instance=reg, initial=initial)
    return render(request, 'adminpanel/registro_form.html', {'form': form, 'create': False, 'reg': reg})


@admin_required
def registro_delete(request, pk):
    try:
        reg = Registro.objects.get(pk=pk)
    except Registro.DoesNotExist:
        messages.error(request, 'Registro no encontrado')
        return redirect('adminpanel:registro_list')
    # Before deleting, check if there are Institucion objects referencing an Administrativo
    # that belongs to this Registro. If so, block deletion and show a helpful message.
    from accounts.models import Administrativo as AdmModel
    from django.db.models import Count
    instituciones_blocking = Institucion.objects.filter(id_adm__id_usu=reg)
    if instituciones_blocking.exists():
        # List institution names to display
        names = [inst.nom_inst for inst in instituciones_blocking]
        messages.error(request, 'No se puede eliminar el registro porque las siguientes instituciones dependen de su administrativo: %s. Asigna otro administrativo a esas instituciones o crea uno nuevo antes de eliminar.' % (', '.join(names)))
        return redirect('adminpanel:registro_list')

    if request.method == 'POST':
        try:
            name = f"{reg.nom_usu} {reg.ape_usu}"
            reg.delete()
            log_action(request, 'delete', 'Registro', object_repr=name)
            messages.success(request, 'Registro eliminado')
        except Exception as e:
            messages.error(request, 'Error al eliminar el registro: %s' % str(e))
        return redirect('adminpanel:registro_list')
    return render(request, 'adminpanel/registro_confirm_delete.html', {'reg': reg})


@admin_required
def registro_change_password(request, pk):
    try:
        reg = Registro.objects.get(pk=pk)
    except Registro.DoesNotExist:
        messages.error(request, 'Registro no encontrado')
        return redirect('adminpanel:registro_list')
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            new_pwd = form.cleaned_data['new_password']
            reg.con_usu = make_password(new_pwd)
            reg.save()
            log_action(request, 'update', 'Registro', object_repr=f"{reg.nom_usu} {reg.ape_usu}", details='password_change')
            messages.success(request, 'Contraseña actualizada')
            return redirect('adminpanel:registro_list')
    else:
        form = PasswordChangeForm()
    return render(request, 'adminpanel/registro_change_password.html', {'form': form, 'reg': reg})


@admin_required
def institucion_list(request):
    q = request.GET.get('q', '').strip()
    # Prefetch the administrativo and its registro to avoid N+1 queries
    qs = Institucion.objects.select_related('id_adm__id_usu').all().order_by('id_inst')
    if q:
        qs = qs.filter(nom_inst__icontains=q)
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    instituciones = paginator.get_page(page)
    return render(request, 'adminpanel/institucion_list.html', {'instituciones': instituciones, 'q': q})


def _get_current_administrativo(request):
    reg_id = request.session.get('registro_id')
    if not reg_id:
        return None
    try:
        reg = Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return None
    from accounts.models import Administrativo as AdmModel
    adm = AdmModel.objects.filter(id_usu=reg).first()
    return adm


def my_instituciones(request):
    # View for administrativos to see institutions linked to them and their requests
    adm = _get_current_administrativo(request)
    if not adm:
        return render(request, 'adminpanel/my_instituciones.html', {'instituciones': [], 'requests': [], 'adm': None})
    insts = Institucion.objects.filter(id_adm=adm)
    reqs = InstitucionRequest.objects.filter(id_adm=adm)
    return render(request, 'adminpanel/my_instituciones.html', {'instituciones': insts, 'requests': reqs, 'adm': adm})


@admin_required
def institucion_maestros(request, pk):
    """Listar y registrar maestros para una institución concreta."""
    try:
        inst = Institucion.objects.get(pk=pk)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada')
        return redirect('adminpanel:institucion_list')

    if request.method == 'POST':
        # fields: nom_usu, ape_usu, ema_usu, password, num_doc_mae, especialidad, foto
        nom = request.POST.get('nom_usu', '').strip()
        ape = request.POST.get('ape_usu', '').strip()
        email = request.POST.get('ema_usu', '').strip()
        password = request.POST.get('password', '').strip()
        num_doc = request.POST.get('num_doc_mae', '').strip()
        especialidad = request.POST.get('especialidad', '').strip()
        foto = request.FILES.get('foto') if hasattr(request, 'FILES') else None

        if not (nom and ape and email and password and num_doc):
            messages.error(request, 'Todos los campos obligatorios deben completarse')
            return redirect('adminpanel:institucion_maestros', pk=pk)

        # Prefer role with id=6 when available, otherwise get or create 'maestro'
        rol = Rol.objects.filter(pk=6).first()
        if not rol:
            rol = Rol.objects.filter(nom_rol__iexact='maestro').first()
            if not rol:
                rol = Rol.objects.create(nom_rol='maestro')

        # ensure email unique
        if Registro.objects.filter(ema_usu=email).exists():
            messages.error(request, 'Ya existe un usuario con ese correo')
            return redirect('adminpanel:institucion_maestros', pk=pk)

        # ensure documento único para maestros
        if Maestro.objects.filter(num_doc_mae=num_doc).exists():
            messages.error(request, 'Ya existe un maestro con ese número de documento')
            return redirect('adminpanel:institucion_maestros', pk=pk)

        reg = Registro.objects.create(
            nom_usu=nom,
            ape_usu=ape,
            ema_usu=email,
            con_usu=make_password(password),
            id_rol=rol
        )

        # create Maestro record
        try:
            mae = Maestro.objects.create(
                num_doc_mae=num_doc,
                especialidad=especialidad or '',
                id_usu=reg,
                id_inst=inst,
                foto_perfil=foto or None
            )
            log_action(request, 'create', 'Maestro', object_repr=f'{mae.num_doc_mae} {reg.nom_usu} {reg.ape_usu}')
            messages.success(request, 'Maestro registrado correctamente')
        except Exception as e:
            # rollback registro if maestro couldn't be created
            reg.delete()
            messages.error(request, 'Error al crear maestro: %s' % str(e))
        return redirect('adminpanel:institucion_maestros', pk=pk)

    maestros = Maestro.objects.filter(id_inst=inst).select_related('id_usu').order_by('id_mae')
    return render(request, 'adminpanel/institucion_maestros.html', {'inst': inst, 'maestros': maestros})


@admin_required
def maestro_edit(request, pk):
    try:
        mae = Maestro.objects.select_related('id_usu', 'id_inst').get(pk=pk)
    except Maestro.DoesNotExist:
        messages.error(request, 'Maestro no encontrado')
        return redirect('adminpanel:institucion_list')

    if request.method == 'POST':
        nom = request.POST.get('nom_usu', '').strip()
        ape = request.POST.get('ape_usu', '').strip()
        email = request.POST.get('ema_usu', '').strip()
        password = request.POST.get('password', '').strip()
        num_doc = request.POST.get('num_doc_mae', '').strip()
        especialidad = request.POST.get('especialidad', '').strip()
        foto = request.FILES.get('foto') if hasattr(request, 'FILES') else None

        if not (nom and ape and email and num_doc):
            messages.error(request, 'Los campos obligatorios no pueden estar vacíos')
            return redirect('adminpanel:maestro_edit', pk=pk)

        # email uniqueness (exclude current)
        if Registro.objects.filter(ema_usu=email).exclude(pk=mae.id_usu.pk).exists():
            messages.error(request, 'El correo ya está en uso por otro usuario')
            return redirect('adminpanel:maestro_edit', pk=pk)

        # documento uniqueness (exclude current)
        if Maestro.objects.filter(num_doc_mae=num_doc).exclude(pk=mae.pk).exists():
            messages.error(request, 'Otro maestro ya usa ese número de documento')
            return redirect('adminpanel:maestro_edit', pk=pk)

        # update registro
        reg = mae.id_usu
        reg.nom_usu = nom
        reg.ape_usu = ape
        reg.ema_usu = email
        if password:
            reg.con_usu = make_password(password)
        reg.save()

        # update maestro
        mae.num_doc_mae = num_doc
        mae.especialidad = especialidad or ''
        if foto:
            mae.foto_perfil = foto
        mae.save()

        log_action(request, 'update', 'Maestro', object_repr=f'{mae.num_doc_mae} {reg.nom_usu} {reg.ape_usu}')
        messages.success(request, 'Maestro actualizado')
        return redirect('adminpanel:institucion_maestros', pk=mae.id_inst.pk)

    # GET -> render form
    return render(request, 'adminpanel/maestro_form.html', {'mae': mae, 'inst': mae.id_inst})


@admin_required
def maestro_delete(request, pk):
    try:
        mae = Maestro.objects.select_related('id_usu', 'id_inst').get(pk=pk)
    except Maestro.DoesNotExist:
        messages.error(request, 'Maestro no encontrado')
        return redirect('adminpanel:institucion_list')

    if request.method == 'POST':
        inst_pk = mae.id_inst.pk if mae.id_inst else None
        # delete maestro and its registro
        try:
            reg = mae.id_usu
            mae.delete()
            # if registro has no related objects, we delete it too — attempt best-effort
            try:
                reg.delete()
            except Exception:
                pass
            log_action(request, 'delete', 'Maestro', object_repr=f'{mae.num_doc_mae}')
            messages.success(request, 'Maestro eliminado')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar maestro: %s' % str(e))
        if inst_pk:
            return redirect('adminpanel:institucion_maestros', pk=inst_pk)
        return redirect('adminpanel:institucion_list')

    return render(request, 'adminpanel/maestro_confirm_delete.html', {'mae': mae})


def request_curso_create(request, pk):
    """Administrativo: propose creating cursos for institution pk."""
    adm = _get_current_administrativo(request)
    if not adm:
        messages.info(request, 'No estás registrado como administrativo para crear solicitudes de cursos.')
        return redirect('adminpanel:my_instituciones')
    try:
        inst = Institucion.objects.get(pk=pk)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada')
        return redirect('adminpanel:my_instituciones')

    if request.method == 'POST':
        form = CursoRequestForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            req = CursoRequest.objects.create(
                id_inst=inst,
                mode=data.get('mode'),
                sections=data.get('sections') or 1,
                cupos=data.get('cupos') or 0,
                start_grade=data.get('start_grade'),
                end_grade=data.get('end_grade'),
                submitted_by=Registro.objects.filter(pk=request.session.get('registro_id')).first()
            )
            # notify admins
            admins = Registro.objects.filter(id_rol__nom_rol__in=['admin', 'administrator', 'administrador'])
            for a in admins:
                try:
                    AdminNotification.objects.create(user=a, title='Nueva solicitud de cursos', message=f'Solicitud para crear cursos en {inst.nom_inst} por {req.submitted_by.nom_usu if req.submitted_by else ""}', curso_request=req)
                    try:
                        send_curso_request_admin(a, req)
                    except Exception:
                        pass
                except Exception:
                    pass
            log_action(request, 'create', 'CursoRequest', object_repr=f'{inst.nom_inst} mode={req.mode} start={req.start_grade} end={req.end_grade}')
            messages.success(request, 'Solicitud de cursos enviada. Un administrador la revisará.')
            return redirect('adminpanel:my_instituciones')
    else:
        form = CursoRequestForm()
    return render(request, 'adminpanel/curso_request_form.html', {'form': form, 'inst': inst})


@admin_required
def administracion_curso_requests(request):
    qs = CursoRequest.objects.all().order_by('-created_at')
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    requests_page = paginator.get_page(page)
    return render(request, 'adminpanel/curso_request_list.html', {'requests': requests_page})


@admin_required
def administracion_curso_request_detail(request, pk):
    try:
        req = CursoRequest.objects.get(pk=pk)
    except CursoRequest.DoesNotExist:
        messages.error(request, 'Solicitud no encontrada')
        return redirect('adminpanel:administracion_curso_requests')
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('reviewer_comments', '')
        reg = Registro.objects.filter(pk=request.session.get('registro_id')).first()
        if action == 'approve':
            # create cursos according to request
            if req.mode == 'primaria':
                start, end = 1, 5
            elif req.mode == 'secundaria':
                start, end = 6, 11
            elif req.mode == 'ambos':
                start, end = 1, 11
            else:
                start, end = req.start_grade or 1, req.end_grade or 1

            created = 0
            skipped = 0
            for grade in range(start, end + 1):
                for s in range(1, (req.sections or 1) + 1):
                    grd_name = f"{grade}-{s:02d}"
                    if Curso.objects.filter(id_inst=req.id_inst, grd_cur=grd_name).exists():
                        skipped += 1
                        continue
                    Curso.objects.create(grd_cur=grd_name, id_inst=req.id_inst, cup_disp_cur=req.cupos)
                    created += 1

            req.status = CursoRequest.STATUS_APPROVED
            req.reviewer = reg
            req.reviewer_comments = comments
            req.save()
            # notify submitter
            if req.submitted_by:
                try:
                    AdminNotification.objects.create(user=req.submitted_by, title='Solicitud de cursos aprobada', message=f'Tu solicitud para {req.id_inst.nom_inst} fue aprobada. Se crearon {created} cursos.', curso_request=req)
                except Exception:
                    pass
            # notify submitter por email
            try:
                if req.submitted_by:
                    send_curso_status_to_submitter(req.submitted_by, req, 'approved', comments or f'Se crearon {created} cursos.')
            except Exception:
                pass
            log_action(request, 'approve', 'CursoRequest', object_repr=f'{req.id_inst.nom_inst} {created} created')
            messages.success(request, f'Solicitud aprobada: {created} cursos creados, {skipped} omitidos.')
            return redirect('adminpanel:administracion_curso_requests')
        elif action == 'request_info':
            req.status = CursoRequest.STATUS_NEEDS_INFO
            req.reviewer = reg
            req.reviewer_comments = comments
            req.save()
            if req.submitted_by:
                msg = 'Se requiere información adicional: ' + (comments or '')
                try:
                    AdminNotification.objects.create(user=req.submitted_by, title='Solicitud de cursos requiere información', message=msg, curso_request=req)
                except Exception:
                    pass
            # notify submitter por email
            try:
                if req.submitted_by:
                    send_curso_status_to_submitter(req.submitted_by, req, 'needs_info', comments)
            except Exception:
                pass
            log_action(request, 'request_info', 'CursoRequest', object_repr=f'{req.id_inst.nom_inst}', details=comments)
            messages.success(request, 'Se solicitó información adicional al solicitante')
            return redirect('adminpanel:administracion_curso_requests')
        elif action == 'reject':
            req.status = CursoRequest.STATUS_REJECTED
            req.reviewer = reg
            req.reviewer_comments = comments
            req.save()
            if req.submitted_by:
                try:
                    AdminNotification.objects.create(user=req.submitted_by, title='Solicitud de cursos rechazada', message=comments or 'La solicitud fue rechazada', curso_request=req)
                except Exception:
                    pass
            # notify submitter por email
            try:
                if req.submitted_by:
                    send_curso_status_to_submitter(req.submitted_by, req, 'rejected', comments)
            except Exception:
                pass
            log_action(request, 'reject', 'CursoRequest', object_repr=f'{req.id_inst.nom_inst}', details=comments)
            messages.success(request, 'Solicitud rechazada')
            return redirect('adminpanel:administracion_curso_requests')
    return render(request, 'adminpanel/curso_request_detail.html', {'req': req})


def request_institucion_create(request):
    adm = _get_current_administrativo(request)
    if not adm:
        messages.info(request, 'No estás registrado como administrativo para crear instituciones. Contacta a un administrador.')
        return redirect('adminpanel:my_instituciones')
    if request.method == 'POST':
        form = InstitucionRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.id_adm = adm
            # set submitted_by if possible
            reg = Registro.objects.filter(pk=request.session.get('registro_id')).first()
            req.submitted_by = reg
            req.save()
            # create admin notifications for all admins
            admins = Registro.objects.filter(id_rol__nom_rol__in=['admin', 'administrator', 'administrador'])
            for a in admins:
                try:
                    AdminNotification.objects.create(user=a, title='Nueva solicitud de institución', message=f'La institución "{req.nom_inst}" fue solicitada por {reg.nom_usu} {reg.ape_usu}. Revisa la solicitud en el panel de auditoría o en Solicitudes de instituciones.', institucion_request=req)
                except Exception:
                    pass
            submitter_name = f"{reg.nom_usu} {reg.ape_usu}" if reg else ''
            log_action(request, 'create', 'InstitucionRequest', object_repr=req.nom_inst, details=f'submitted_by={submitter_name}')
            messages.success(request, 'Solicitud enviada. Un administrador revisará la información.')
            return redirect('adminpanel:my_instituciones')
    else:
        form = InstitucionRequestForm()
    return render(request, 'adminpanel/institucion_request_form.html', {'form': form, 'adm': adm})


@admin_required
def curso_horario(request, pk):
    """Permite ver y editar (añadir) asignaturas y horarios para un curso."""
    try:
        curso = Curso.objects.select_related('id_inst').get(pk=pk)
    except Curso.DoesNotExist:
        messages.error(request, 'Curso no encontrado')
        return redirect('adminpanel:curso_list')

    # simple inline forms without a dedicated Form class
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_asignatura':
            nombre = request.POST.get('nombre', '').strip()
            if nombre:
                # reuse existing global asignatura (case-insensitive) to avoid duplicates
                asign = Asignatura.objects.filter(nombre__iexact=nombre).first()
                if asign:
                    messages.info(request, 'Asignatura ya existe y será reutilizada')
                else:
                    asign = Asignatura.objects.create(nombre=nombre)
                    log_action(request, 'create', 'Asignatura', object_repr=f'{asign.nombre} for curso {curso.id_cur}')
                    messages.success(request, 'Asignatura creada')
            else:
                messages.error(request, 'El nombre de la asignatura no puede estar vacío')
            return redirect('adminpanel:curso_horario', pk=pk)

        if action == 'add_slot':
            try:
                asig_id = int(request.POST.get('asignatura'))
                dia = int(request.POST.get('dia'))
                hora_inicio = request.POST.get('hora_inicio') or None
                hora_fin = request.POST.get('hora_fin') or None
                aula = request.POST.get('aula', '').strip() or None
                asign = Asignatura.objects.get(pk=asig_id)
                mae_id = request.POST.get('maestro')
                maestro_obj = None
                if mae_id:
                    try:
                        maestro_obj = Maestro.objects.get(pk=int(mae_id))
                    except Exception:
                        maestro_obj = None
                # validation: prevent same asignatura at same course/day/start time unless institution allows duplicates
                inst = getattr(curso, 'id_inst', None)
                allow_dup = False
                try:
                    allow_dup = bool(getattr(inst, 'allow_duplicate_subject_slots', False))
                except Exception:
                    allow_dup = False
                if not allow_dup:
                    exists = Horario.objects.filter(id_cur=curso, dia=dia, hora_inicio=hora_inicio, id_asig=asign).exists()
                    if exists:
                        messages.error(request, 'No se puede agregar: la asignatura ya tiene una franja en ese día y hora (desactiva la validación si es necesario).')
                        return redirect('adminpanel:curso_horario', pk=pk)
                Horario.objects.create(id_asig=asign, id_cur=curso, id_mae=maestro_obj, dia=dia, hora_inicio=hora_inicio or None, hora_fin=hora_fin or None, aula=aula)
                messages.success(request, 'Horario agregado')
            except Exception as e:
                messages.error(request, 'Error al agregar horario: %s' % str(e))
            return redirect('adminpanel:curso_horario', pk=pk)
        if action == 'delete_asignatura':
            try:
                asig_id = int(request.POST.get('asig_id'))
                asign = Asignatura.objects.get(pk=asig_id)
                nombre = asign.nombre
                asign.delete()
                log_action(request, 'delete', 'Asignatura', object_repr=nombre)
                messages.success(request, 'Asignatura eliminada')
            except Exception as e:
                messages.error(request, 'No se pudo eliminar la asignatura: %s' % str(e))
            return redirect('adminpanel:curso_horario', pk=pk)
        if action == 'delete_slot':
            try:
                hor_id = int(request.POST.get('hor_id'))
                h = Horario.objects.get(pk=hor_id, id_cur=curso)
                h.delete()
                log_action(request, 'delete', 'Horario', object_repr=f'hora id {hor_id}')
                messages.success(request, 'Franja horaria eliminada')
            except Exception as e:
                messages.error(request, 'No se pudo eliminar la franja horaria: %s' % str(e))
            return redirect('adminpanel:curso_horario', pk=pk)
        if action == 'toggle_dup_check':
            try:
                inst = getattr(curso, 'id_inst', None)
                if inst:
                    inst.allow_duplicate_subject_slots = not bool(getattr(inst, 'allow_duplicate_subject_slots', False))
                    inst.save()
                    messages.success(request, f"Validación duplicados {'desactivada' if inst.allow_duplicate_subject_slots else 'activada'} para {inst.nom_inst}")
            except Exception as e:
                messages.error(request, 'No se pudo cambiar la configuración: %s' % str(e))
            return redirect('adminpanel:curso_horario', pk=pk)

    # show global pool of asignaturas so administrativos can reuse existing entries
    asignaturas = Asignatura.objects.all().order_by('nombre')
    horarios = Horario.objects.filter(id_cur=curso).select_related('id_asig', 'id_mae').order_by('dia', 'hora_inicio')
    maestros = Maestro.objects.filter(id_inst=curso.id_inst).select_related('id_usu').order_by('id_usu__nom_usu')

    # build a simple day->list mapping for template convenience
    days = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes'}

    # annotate horarios with human-readable day to simplify template
    for h in horarios:
        try:
            h.dia_display = days.get(h.dia, str(h.dia))
        except Exception:
            h.dia_display = str(h.dia)

    return render(request, 'adminpanel/curso_horario.html', {
        'curso': curso,
        'asignaturas': asignaturas,
        'horarios': horarios,
        'maestros': maestros,
        'days': days,
    })


@admin_required
def administracion_institucion_requests(request):
    # Admin list of requests
    qs = InstitucionRequest.objects.all().order_by('-created_at')
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    requests_page = paginator.get_page(page)
    return render(request, 'adminpanel/institucion_request_list.html', {'requests': requests_page})


@admin_required
def administracion_institucion_request_detail(request, pk):
    try:
        req = InstitucionRequest.objects.get(pk=pk)
    except InstitucionRequest.DoesNotExist:
        messages.error(request, 'Solicitud no encontrada')
        return redirect('adminpanel:administracion_institucion_requests')
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('reviewer_comments', '')
        reg = Registro.objects.filter(pk=request.session.get('registro_id')).first()
        if action == 'approve':
            # create real Institucion
            inst = Institucion.objects.create(
                nom_inst=req.nom_inst,
                tip_inst=req.tip_inst or '',
                cod_dane_inst=req.cod_dane_inst or '',
                dep_inst=req.dep_inst or '',
                mun_inst=req.mun_inst or '',
                dire_inst=req.dire_inst or '',
                tel_inst=req.tel_inst or '',
                ema_inst=req.ema_inst or '',
                id_adm=req.id_adm
            )
            req.status = InstitucionRequest.STATUS_APPROVED
            req.reviewer = reg
            req.reviewer_comments = comments
            req.save()
            # notify submitter
            if req.submitted_by:
                try:
                    AdminNotification.objects.create(user=req.submitted_by, title='Solicitud aprobada', message=f'Tu solicitud para "{req.nom_inst}" ha sido aprobada.', institucion_request=req)
                except Exception:
                    pass
            # notify administrativo de la institución (si existe)
            try:
                admin_reg = getattr(req.id_adm, 'id_usu', None)
                if admin_reg:
                    send_institucion_status_email(admin_reg, req, 'approved', comments)
            except Exception:
                pass
            log_action(request, 'approve', 'InstitucionRequest', object_repr=req.nom_inst)
            messages.success(request, 'Solicitud aprobada y institución creada')
            return redirect('adminpanel:administracion_institucion_requests')
        elif action == 'request_info':
            # mark needs info and save comments
            req.status = InstitucionRequest.STATUS_NEEDS_INFO
            req.reviewer = reg
            req.reviewer_comments = comments
            req.save()
            # notify submitter with missing fields or comments
            if req.submitted_by:
                missing = req.missing_fields()
                msg = comments
                if missing:
                    msg = 'Faltan los siguientes datos: ' + ', '.join(missing) + ('. ' + comments if comments else '')
                try:
                    AdminNotification.objects.create(user=req.submitted_by, title='Solicitud requiere información', message=msg, institucion_request=req)
                except Exception:
                    pass
            # notify administrativo de la institución (si existe)
            try:
                admin_reg = getattr(req.id_adm, 'id_usu', None)
                if admin_reg:
                    send_institucion_status_email(admin_reg, req, 'needs_info', comments)
            except Exception:
                pass
            log_action(request, 'request_info', 'InstitucionRequest', object_repr=req.nom_inst, details=comments)
            messages.success(request, 'Se solicitó información adicional al solicitante')
            return redirect('adminpanel:administracion_institucion_requests')
        elif action == 'reject':
            req.status = InstitucionRequest.STATUS_REJECTED
            req.reviewer = reg
            req.reviewer_comments = comments
            req.save()
            if req.submitted_by:
                try:
                    AdminNotification.objects.create(user=req.submitted_by, title='Solicitud rechazada', message=comments or 'La solicitud fue rechazada por el administrador', institucion_request=req)
                except Exception:
                    pass
            # notify administrativo de la institución (si existe)
            try:
                admin_reg = getattr(req.id_adm, 'id_usu', None)
                if admin_reg:
                    send_institucion_status_email(admin_reg, req, 'rejected', comments)
            except Exception:
                pass
            log_action(request, 'reject', 'InstitucionRequest', object_repr=req.nom_inst, details=comments)
            messages.success(request, 'Solicitud rechazada')
            return redirect('adminpanel:administracion_institucion_requests')
    return render(request, 'adminpanel/institucion_request_detail.html', {'req': req})


def _get_current_registro(request):
    reg_id = request.session.get('registro_id')
    if not reg_id:
        return None
    try:
        return Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return None


def notifications_list(request):
    """List notifications for the current logged Registro (paginated)."""
    reg = _get_current_registro(request)
    if not reg:
        messages.error(request, 'Debes iniciar sesión para ver notificaciones')
        return redirect('accounts:login')
    qs = AdminNotification.objects.filter(user=reg).order_by('-timestamp')
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    notes = paginator.get_page(page)
    return render(request, 'adminpanel/notifications_list.html', {'notifications': notes})


def notification_mark_read(request, pk):
    reg = _get_current_registro(request)
    if not reg:
        return redirect('accounts:login')
    try:
        n = AdminNotification.objects.get(pk=pk, user=reg)
    except AdminNotification.DoesNotExist:
        messages.error(request, 'Notificación no encontrada')
        return redirect('adminpanel:notifications')
    n.is_read = True
    n.save()
    return redirect('adminpanel:notifications')


def notification_mark_all_read(request):
    reg = _get_current_registro(request)
    if not reg:
        return redirect('accounts:login')
    AdminNotification.objects.filter(user=reg, is_read=False).update(is_read=True)
    return redirect('adminpanel:notifications')


def notification_detail(request, pk):
    reg = _get_current_registro(request)
    if not reg:
        return redirect('accounts:login')
    try:
        # obtener la notificación sin filtrar por usuario para permitir que
        # administrativos globales o el administrativo vinculado a la institución la abran
        n = AdminNotification.objects.get(pk=pk)
    except AdminNotification.DoesNotExist:
        messages.error(request, 'Notificación no encontrada')
        return redirect('adminpanel:notifications')

    # permiso: permitir si la notificación pertenece al registro, o si el
    # registro tiene rol 'admin'/'administrator', o si el registro es el
    # administrativo vinculado a la institución de la solicitud.
    rol_name = (reg.id_rol.nom_rol or '').lower() if reg and reg.id_rol else ''
    # treat explicit admin roles only (avoid matching 'administrativo')
    is_admin_role = rol_name in ('admin', 'administrator', 'administrador')
    allowed = False
    try:
        if n.user_id == getattr(reg, 'id', None) or (getattr(reg, 'id_usu', None) and n.user_id == getattr(reg.id_usu, 'id', None)):
            allowed = True
    except Exception:
        if n.user_id == getattr(reg, 'id', None):
            allowed = True
    if is_admin_role:
        allowed = True
    try:
        if not allowed and getattr(n, 'matricula_request', None):
            inst_admin = getattr(n.matricula_request.id_inst, 'id_adm', None)
            if inst_admin and getattr(inst_admin, 'id_usu', None) and reg and getattr(inst_admin.id_usu, 'id', None) == getattr(reg, 'id', None):
                allowed = True
    except Exception:
        pass

    # allow the administrativo linked to an InstitucionRequest to open it
    try:
        if not allowed and getattr(n, 'institucion_request', None):
            inst_admin = getattr(n.institucion_request, 'id_adm', None)
            if inst_admin and getattr(inst_admin, 'id_usu', None) and reg and getattr(inst_admin.id_usu, 'id_usu', None) == getattr(reg, 'id_usu', None):
                allowed = True
    except Exception:
        pass

    if not allowed:
        # debug output for console (useful during development)
        print(f"DEBUG notification_detail: access denied n.id={getattr(n,'id',None)} n.user_id={getattr(n,'user_id',None)} matricula_request_id={getattr(n,'matricula_request_id',None)} reg_id={getattr(reg,'id',None)} rol={rol_name}")
        messages.error(request, 'No tienes permiso para ver esta notificación')
        return redirect('adminpanel:notifications')

    # mark read
    n.is_read = True
    n.save()
    print(f"DEBUG notification_detail: opening n.id={n.id} matricula_request_id={getattr(n,'matricula_request_id',None)} user_id={n.user_id} reg_id={getattr(reg,'id',None)} rol={rol_name}")

    # if linked to InstitucionRequest, redirect to appropriate detail view
    if getattr(n, 'institucion_request_id', None):
        rol_name = (reg.id_rol.nom_rol or '').lower() if reg.id_rol else ''
        if rol_name in ('admin', 'administrator'):
            return redirect('adminpanel:administracion_institucion_request_detail', pk=n.institucion_request_id)
        else:
            return redirect('adminpanel:institucion_request_public', pk=n.institucion_request_id)

    # if linked to CursoRequest, redirect to appropriate detail view
    if getattr(n, 'curso_request_id', None):
        rol_name = (reg.id_rol.nom_rol or '').lower() if reg.id_rol else ''
        if rol_name in ('admin', 'administrator'):
            return redirect('adminpanel:administracion_curso_request_detail', pk=n.curso_request_id)
        else:
            return redirect('adminpanel:curso_request_public', pk=n.curso_request_id)

    # if linked to MatriculaRequest, redirect to matricula detail in admin
    if getattr(n, 'matricula_request_id', None):
        rol_name = (reg.id_rol.nom_rol or '').lower() if reg and reg.id_rol else ''
        if rol_name in ('admin', 'administrator'):
            return redirect('adminpanel:matricula_request_detail', pk=n.matricula_request_id)
        else:
            return redirect('adminpanel:notifications')

    return redirect('adminpanel:notifications')


def institucion_request_public_view(request, pk):
    # Allow the submitter to view the request and the reviewer's comments
    reg = _get_current_registro(request)
    try:
        req = InstitucionRequest.objects.get(pk=pk)
    except InstitucionRequest.DoesNotExist:
        messages.error(request, 'Solicitud no encontrada')
        return redirect('adminpanel:notifications')
    # allow if current registro is the submitter or is admin
    if reg and req.submitted_by and reg.id_usu == req.submitted_by.id_usu:
        # show public read-only detail with reviewer comments and missing fields
        missing = req.missing_fields()
        return render(request, 'adminpanel/institucion_request_public.html', {'req': req, 'missing': missing})
    # if admin, redirect to admin detail
    rol_name = (reg.id_rol.nom_rol or '').lower() if reg and reg.id_rol else ''
    if rol_name in ('admin', 'administrator'):
        return redirect('adminpanel:administracion_institucion_request_detail', pk=pk)
    messages.error(request, 'No tienes permiso para ver esta solicitud')
    return redirect('adminpanel:notifications')


@admin_required
def matricula_request_detail(request, pk):
    try:
        req = MatriculaRequest.objects.get(pk=pk)
    except MatriculaRequest.DoesNotExist:
        messages.error(request, 'Solicitud no encontrada')
        return redirect('adminpanel:notifications')

    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        # registrar comentario en la solicitud y cambiar estado
        if comment:
            req.obs = (req.obs or '') + '\n' + comment
        if action == 'accept':
            req.estado = 'accepted'
            # guardar observaciones en la solicitud
            req.obs = (req.obs or '') + ('\n' + comment if comment else '')
            req.save()
            # seleccionar curso disponible automáticamente
            assigned_course = None
            try:
                # intentar por grado solicitado (e.g. '6' -> cursos que empiezan por '6-')
                if req.grado_solicitado:
                    pref = str(int(req.grado_solicitado)) + '-'
                    qs = Curso.objects.filter(id_inst=req.id_inst, grd_cur__startswith=pref, cup_disp_cur__gt=0)
                    if qs.exists():
                        assigned_course = random.choice(list(qs))
                # fallback: cualquier curso con cupo
                if not assigned_course:
                    qs2 = Curso.objects.filter(id_inst=req.id_inst, cup_disp_cur__gt=0)
                    if qs2.exists():
                        assigned_course = random.choice(list(qs2))
                # si se asignó, descontar cupo
                if assigned_course:
                    assigned_course.cup_disp_cur = max(0, assigned_course.cup_disp_cur - 1)
                    assigned_course.save()
            except Exception:
                assigned_course = None

            # crear matrícula con datos y observaciones
            try:
                mat = Matricula.objects.create(
                    fch_reg_mat=timezone.now().date(),
                    id_est=req.id_est,
                    id_cur=assigned_course if assigned_course else None,
                    grado_solicitado=req.grado_solicitado,
                    est_mat='activo',
                    obs_mat=comment or ''
                )
            except Exception:
                mat = None

            messages.success(request, 'Solicitud aceptada y matrícula creada' + (f' (curso asignado: {assigned_course.grd_cur})' if assigned_course else ' (sin curso asignado - sin cupos)'))
            # notificar al acudiente
            try:
                from adminpanel.models import AdminNotification
                if getattr(req.id_acu, 'id_usu', None):
                    # enviar mensaje al acudiente sin exponer IDs: mostrar estado claro y nombre del estudiante
                    estudiante_nombre = f"{req.id_est.id_usu.nom_usu} {req.id_est.id_usu.ape_usu}" if getattr(req, 'id_est', None) and getattr(req.id_est, 'id_usu', None) else 'el estudiante'
                    AdminNotification.objects.create(
                        user=req.id_acu.id_usu,
                        title='Solicitud de matrícula aceptada',
                        message=f'Su solicitud de matrícula para {estudiante_nombre} ha sido aprobada. {comment or ""}'.strip()
                    )
                    # enviar email al acudiente informando resultado
                    try:
                        from communications.email_utils import send_matricula_status_to_acudiente
                        acudiente_reg = req.id_acu.id_usu
                        send_matricula_status_to_acudiente(acudiente_reg, req, 'accepted', comment=comment, assigned_course=assigned_course)
                    except Exception:
                        pass
            except Exception:
                pass
            return redirect('adminpanel:notifications')
        elif action == 'reject':
            req.estado = 'rejected'
            req.save()
            try:
                from adminpanel.models import AdminNotification
                if getattr(req.id_acu, 'id_usu', None):
                    estudiante_nombre = f"{req.id_est.id_usu.nom_usu} {req.id_est.id_usu.ape_usu}" if getattr(req, 'id_est', None) and getattr(req.id_est, 'id_usu', None) else 'el estudiante'
                    AdminNotification.objects.create(
                        user=req.id_acu.id_usu,
                        title='Solicitud de matrícula rechazada',
                        message=f'Su solicitud de matrícula para {estudiante_nombre} ha sido rechazada. {comment or ""}'.strip()
                    )
                    # enviar email al acudiente informando rechazo
                    try:
                        from communications.email_utils import send_matricula_status_to_acudiente
                        acudiente_reg = req.id_acu.id_usu
                        send_matricula_status_to_acudiente(acudiente_reg, req, 'rejected', comment=comment)
                    except Exception:
                        pass
            except Exception:
                pass
            messages.success(request, 'Solicitud rechazada')
            return redirect('adminpanel:notifications')
        elif action == 'hold':
            req.estado = 'pending'
            req.save()
            # Notificar al acudiente que la solicitud quedó en espera
            try:
                from adminpanel.models import AdminNotification
                if getattr(req.id_acu, 'id_usu', None):
                    estudiante_nombre = (
                        f"{req.id_est.id_usu.nom_usu} {req.id_est.id_usu.ape_usu}"
                        if getattr(req, 'id_est', None) and getattr(req.id_est, 'id_usu', None)
                        else 'el estudiante'
                    )
                    AdminNotification.objects.create(
                        user=req.id_acu.id_usu,
                        title='Solicitud de matrícula en espera',
                        message=f'Su solicitud de matrícula para {estudiante_nombre} ha sido marcada EN ESPERA para revisión adicional.'
                    )
                    # enviar email al acudiente informando estado en espera
                    try:
                        from communications.email_utils import send_matricula_status_to_acudiente
                        acudiente_reg = req.id_acu.id_usu
                        send_matricula_status_to_acudiente(acudiente_reg, req, 'pending', comment='En espera para revisión adicional')
                    except Exception:
                        pass
            except Exception:
                pass
            messages.success(request, 'Solicitud puesta en espera')
            return redirect('adminpanel:notifications')

    # recolectar documentos relacionados al estudiante (incluye por id_est y últimos vinculados a matrícula previa)
    docs_qs = Documento.objects.filter(id_est=req.id_est).order_by('-id_doc')
    docs_list = []
    image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    for d in docs_qs:
        # para cada Documento, convertir sus campos en pares label/valor
        row = []
        for field in ['reg_civil_doc', 'doc_idn_acu', 'doc_idn_alum', 'cnt_vac_doc', 'adres_doc', 'fot_alum_doc', 'visa_extr_doc', 'cer_med_disca_doc', 'cer_esc_doc']:
            val = getattr(d, field, None)
            if val:
                is_image = False
                try:
                    is_image = str(val).lower().endswith(image_exts)
                except Exception:
                    is_image = False
                row.append({
                    'field': field,
                    'value': val,
                    'is_image': is_image,
                })
        if row:
            docs_list.append({'doc': d, 'items': row})

    return render(request, 'adminpanel/matricula_request_detail.html', {'req': req, 'docs_list': docs_list, 'MEDIA_URL': settings.MEDIA_URL})


def curso_request_public_view(request, pk):
    # Allow the submitter to view the course request and the reviewer's comments
    reg = _get_current_registro(request)
    try:
        req = CursoRequest.objects.get(pk=pk)
    except CursoRequest.DoesNotExist:
        messages.error(request, 'Solicitud de curso no encontrada')
        return redirect('adminpanel:notifications')
    # allow if current registro is the submitter or is admin
    if reg and req.submitted_by and reg.id_usu == req.submitted_by.id_usu:
        missing = req.missing_fields()
        return render(request, 'adminpanel/curso_request_public.html', {'req': req, 'missing': missing})
    rol_name = (reg.id_rol.nom_rol or '').lower() if reg and reg.id_rol else ''
    if rol_name in ('admin', 'administrator'):
        return redirect('adminpanel:administracion_curso_request_detail', pk=pk)
    messages.error(request, 'No tienes permiso para ver esta solicitud')
    return redirect('adminpanel:notifications')


@admin_required
def institucion_create(request):
    from .forms import InstitucionForm
    if request.method == 'POST':
        form = InstitucionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Institución creada correctamente')
            return redirect('adminpanel:institucion_list')
    else:
        form = InstitucionForm()
    return render(request, 'adminpanel/institucion_form.html', {'form': form, 'create': True})


@admin_required
def institucion_edit(request, pk):
    from .forms import InstitucionForm
    try:
        inst = Institucion.objects.get(pk=pk)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada')
        return redirect('adminpanel:institucion_list')
    if request.method == 'POST':
        form = InstitucionForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            messages.success(request, 'Institución actualizada')
            return redirect('adminpanel:institucion_list')
    else:
        form = InstitucionForm(instance=inst)
    return render(request, 'adminpanel/institucion_form.html', {'form': form, 'create': False, 'inst': inst})


@admin_required
def institucion_delete(request, pk):
    try:
        inst = Institucion.objects.get(pk=pk)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada')
        return redirect('adminpanel:institucion_list')
    # prevent deletion if there are related objects (cursos u otras relaciones inversas)
    has_related = False
    related_examples = []
    for rel in inst._meta.get_fields():
        # check reverse one-to-many, one-to-one and m2m relations
        if getattr(rel, 'auto_created', False) and (rel.one_to_many or rel.one_to_one or rel.many_to_many):
            accessor = rel.get_accessor_name()
            related_manager = getattr(inst, accessor, None)
            if related_manager is None:
                continue
            try:
                if related_manager.exists():
                    has_related = True
                    related_examples.append(rel.related_model.__name__)
                    break
            except Exception:
                continue
    if has_related:
        messages.error(request, 'No se puede eliminar la institución porque tiene objetos relacionados: %s' % (', '.join(related_examples)))
        return redirect('adminpanel:institucion_list')
    if request.method == 'POST':
        try:
            inst.delete()
            messages.success(request, 'Institución eliminada')
        except IntegrityError:
            messages.error(request, 'Error al eliminar la institución')
        return redirect('adminpanel:institucion_list')
    return render(request, 'adminpanel/institucion_confirm_delete.html', {'inst': inst})


@admin_required
def institucion_bulk_cursos(request, pk):
    from .forms import BulkCursoForm
    try:
        inst = Institucion.objects.get(pk=pk)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada')
        return redirect('adminpanel:institucion_list')

    if request.method == 'POST':
        form = BulkCursoForm(request.POST)
        if form.is_valid():
            mode = form.cleaned_data['mode']
            sections = form.cleaned_data['sections']
            if mode == 'primaria':
                start, end = 1, 5
            elif mode == 'secundaria':
                start, end = 6, 11
            elif mode == 'ambos':
                start, end = 1, 11
            else:
                start = form.cleaned_data.get('start_grade')
                end = form.cleaned_data.get('end_grade')

            created = 0
            skipped = 0
            for grade in range(start, end + 1):
                for s in range(1, sections + 1):
                    grd_name = f"{grade}-{s:02d}"
                    # avoid duplicates for this institution
                    if Curso.objects.filter(id_inst=inst, grd_cur=grd_name).exists():
                        skipped += 1
                        continue
                    # set default cupos per curso
                    cupos = form.cleaned_data.get('cupos') or 0
                    Curso.objects.create(grd_cur=grd_name, id_inst=inst, cup_disp_cur=cupos)
                    created += 1

            messages.success(request, f'Operación completada: {created} cursos creados, {skipped} omitidos (ya existían)')
            # audit
            log_action(request, 'create', 'Curso', object_repr=f'{created} cursos en {inst.nom_inst}', details=f'bulk_mode={mode} sections={sections} start={start} end={end}')
            return redirect('adminpanel:institucion_list')
    else:
        form = BulkCursoForm()
    return render(request, 'adminpanel/institucion_bulk_cursos.html', {'form': form, 'inst': inst})


@admin_required
def institucion_clear_cursos(request, pk):
    try:
        inst = Institucion.objects.get(pk=pk)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada')
        return redirect('adminpanel:institucion_list')

    curso_count = Curso.objects.filter(id_inst=inst).count()
    if request.method == 'POST':
        # delete all cursos for this institution
        deleted, _ = Curso.objects.filter(id_inst=inst).delete()
        messages.success(request, f'Se eliminaron {deleted} objetos relacionados (cursos) para la institución')
        log_action(request, 'delete', 'Curso', object_repr=f'{deleted} cursos de {inst.nom_inst}', details='clear_all')
        return redirect('adminpanel:institucion_list')

    return render(request, 'adminpanel/institucion_clear_cursos_confirm.html', {'inst': inst, 'curso_count': curso_count})


@admin_required
def curso_list(request):
    q = request.GET.get('q', '').strip()
    # annotate with number of matriculas (students) to display current enrollment count
    qs = Curso.objects.select_related('id_inst').annotate(student_count=Count('matricula')).all().order_by('id_cur')
    if q:
        qs = qs.filter(grd_cur__icontains=q)
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    cursos = paginator.get_page(page)
    return render(request, 'adminpanel/curso_list.html', {'cursos': cursos, 'q': q})


def curso_matriculas(request, pk):
    """Mostrar la lista de matriculas (estudiantes) para un curso concreto."""
    from school.models import Curso, Matricula
    try:
        curso = Curso.objects.get(pk=pk)
    except Curso.DoesNotExist:
        messages.error(request, 'Curso no encontrado')
        return redirect('adminpanel:curso_list')

    matriculas = Matricula.objects.filter(id_cur=curso).select_related('id_est__id_usu').order_by('-fch_reg_mat')
    total = matriculas.count()
    return render(request, 'adminpanel/curso_matriculas.html', {'curso': curso, 'matriculas': matriculas, 'total': total})


def curso_list_by_institucion(request, pk):
    # Allow admins or the administrative owner of the institution to view its cursos
    try:
        inst = Institucion.objects.get(pk=pk)
    except Institucion.DoesNotExist:
        messages.error(request, 'Institución no encontrada')
        return redirect('accounts:dashboard')

    # permission: admins can view; administrativos linked to the institution can view
    reg = _get_current_registro(request)
    rol_name = (reg.id_rol.nom_rol or '').lower() if reg and reg.id_rol else ''
    is_global_admin = rol_name in ('admin', 'administrator')
    if not is_global_admin:
        adm = _get_current_administrativo(request)
        if not adm or inst.id_adm_id != adm.id_adm:
            messages.error(request, 'No tienes permiso para ver los cursos de esta institución')
            return redirect('accounts:dashboard')

    q = request.GET.get('q', '').strip()
    qs = Curso.objects.filter(id_inst=inst).select_related('id_inst').annotate(student_count=Count('matricula')).order_by('id_cur')
    if q:
        qs = qs.filter(grd_cur__icontains=q)
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    cursos = paginator.get_page(page)
    # allow bulk creation only for global admins (not for administrativos)
    return render(request, 'adminpanel/curso_list.html', {'cursos': cursos, 'q': q, 'institucion': inst, 'can_bulk_create': is_global_admin})


@admin_required
def curso_create(request):
    from .forms import CursoForm
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            cur = form.save()
            log_action(request, 'create', 'Curso', object_repr=cur.grd_cur, details=f'institucion={cur.id_inst.nom_inst if cur.id_inst else ""}')
            messages.success(request, 'Curso creado correctamente')
            return redirect('adminpanel:curso_list')
    else:
        form = CursoForm()
    return render(request, 'adminpanel/curso_form.html', {'form': form, 'create': True})


@admin_required
def curso_edit(request, pk):
    from .forms import CursoForm
    try:
        cur = Curso.objects.get(pk=pk)
    except Curso.DoesNotExist:
        messages.error(request, 'Curso no encontrado')
        return redirect('adminpanel:curso_list')
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=cur)
        if form.is_valid():
            cur = form.save()
            log_action(request, 'update', 'Curso', object_repr=cur.grd_cur, details=f'institucion={cur.id_inst.nom_inst if cur.id_inst else ""}')
            messages.success(request, 'Curso actualizado')
            return redirect('adminpanel:curso_list')
    else:
        form = CursoForm(instance=cur)
    return render(request, 'adminpanel/curso_form.html', {'form': form, 'create': False, 'cur': cur})


@admin_required
def curso_delete(request, pk):
    try:
        cur = Curso.objects.get(pk=pk)
    except Curso.DoesNotExist:
        messages.error(request, 'Curso no encontrado')
        return redirect('adminpanel:curso_list')
    if request.method == 'POST':
        name = str(cur.grd_cur)
        inst_name = cur.id_inst.nom_inst if cur.id_inst else ''
        cur.delete()
        log_action(request, 'delete', 'Curso', object_repr=name, details=f'institucion={inst_name}')
        messages.success(request, 'Curso eliminado')
        return redirect('adminpanel:curso_list')
    return render(request, 'adminpanel/curso_confirm_delete.html', {'cur': cur})


@admin_required
def administrativo_list(request):
    q = request.GET.get('q', '').strip()
    qs = AdministrativoModel.objects.select_related('id_usu').all().order_by('id_adm')
    if q:
        qs = qs.filter(num_doc_adm__icontains=q)
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    administrativos = paginator.get_page(page)
    return render(request, 'adminpanel/administrativo_list.html', {'administrativos': administrativos, 'q': q})


@admin_required
def administrativo_create(request):
    from .forms import AdministrativoForm
    if request.method == 'POST':
        form = AdministrativoForm(request.POST, request.FILES)
        if form.is_valid():
            adm = form.save()
            log_action(request, 'create', 'Administrativo', object_repr=adm.num_doc_adm)
            messages.success(request, 'Administrativo creado correctamente')
            return redirect('adminpanel:administrativo_list')
    else:
        form = AdministrativoForm()
    return render(request, 'adminpanel/administrativo_form.html', {'form': form, 'create': True})


@admin_required
def administrativo_edit(request, pk):
    from .forms import AdministrativoForm
    try:
        adm = AdministrativoModel.objects.get(pk=pk)
    except AdministrativoModel.DoesNotExist:
        messages.error(request, 'Administrativo no encontrado')
        return redirect('adminpanel:administrativo_list')
    if request.method == 'POST':
        form = AdministrativoForm(request.POST, request.FILES, instance=adm)
        if form.is_valid():
            adm = form.save()
            log_action(request, 'update', 'Administrativo', object_repr=adm.num_doc_adm)
            messages.success(request, 'Administrativo actualizado')
            return redirect('adminpanel:administrativo_list')
    else:
        form = AdministrativoForm(instance=adm)
    return render(request, 'adminpanel/administrativo_form.html', {'form': form, 'create': False, 'adm': adm})


@admin_required
def administrativo_delete(request, pk):
    try:
        adm = AdministrativoModel.objects.get(pk=pk)
    except AdministrativoModel.DoesNotExist:
        messages.error(request, 'Administrativo no encontrado')
        return redirect('adminpanel:administrativo_list')
    if request.method == 'POST':
        num = adm.num_doc_adm
        adm.delete()
        log_action(request, 'delete', 'Administrativo', object_repr=num)
        messages.success(request, 'Administrativo eliminado')
        return redirect('adminpanel:administrativo_list')
    return render(request, 'adminpanel/administrativo_confirm_delete.html', {'adm': adm})


@admin_required
def registro_export_csv(request):
    qs = Registro.objects.all().order_by('id_usu')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="registros.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nombre', 'Apellido', 'Email', 'Rol'])
    for r in qs:
        writer.writerow([r.id_usu, r.nom_usu, r.ape_usu, r.ema_usu, r.id_rol.nom_rol if r.id_rol else ''])
    log_action(request, 'export', 'Registro', object_repr='all', details='export_csv')
    return response


@admin_required
def curso_export_csv(request):
    qs = Curso.objects.select_related('id_inst').annotate(student_count=Count('matricula')).all().order_by('id_cur')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cursos.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Grado', 'Cupos', 'Inscritos', 'Institucion'])
    for c in qs:
        writer.writerow([c.id_cur, c.grd_cur, c.cup_disp_cur, getattr(c, 'student_count', 0), c.id_inst.nom_inst if c.id_inst else ''])
    log_action(request, 'export', 'Curso', object_repr='all', details='export_csv')
    return response


@admin_required
def admin_logs(request):
    # Logs list with simple filters: model, action, q (search in object_repr/details), user
    try:
        qs = AdminActionLog.objects.select_related('user').all()
        model = request.GET.get('model')
        action = request.GET.get('action')
        q = request.GET.get('q', '').strip()
        user = request.GET.get('user')
        if model:
            qs = qs.filter(model_name__iexact=model)
        if action:
            qs = qs.filter(action__iexact=action)
        if user:
            qs = qs.filter(user__id_usu=user)
        if q:
            qs = qs.filter(Q(object_repr__icontains=q) | Q(details__icontains=q))
        qs = qs.order_by('-timestamp')
        paginator = Paginator(qs, 30)
        page = request.GET.get('page')
        logs = paginator.get_page(page)
        # possible filters lists
        models_list = AdminActionLog.objects.values_list('model_name', flat=True).distinct()
    except OperationalError:
        # If migrations haven't been applied, the table won't exist yet — avoid crashing.
        messages.warning(request, 'El sistema de auditoría aún no está disponible (tabla faltante). Ejecuta migraciones para habilitarlo.')
        # Provide an empty page-like object so the template pagination doesn't break
        empty_list = []
        paginator = Paginator(empty_list, 30)
        logs = paginator.get_page(1)
        models_list = []
        model = request.GET.get('model')
        action = request.GET.get('action')
        q = request.GET.get('q', '').strip()
        user = request.GET.get('user')

    return render(request, 'adminpanel/logs_list.html', {'logs': logs, 'models_list': models_list, 'q': q, 'model': model, 'action': action, 'user': user})
