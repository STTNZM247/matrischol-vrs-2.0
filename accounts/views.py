from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from .forms import RegistroForm, LoginForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import Registro, Rol, Administrativo, PasswordResetRequest
from django.contrib.auth.hashers import make_password, check_password
from people.models import Acudiente, Estudiante
from django.db.models import Q
from django.conf import settings
from django.core.files.storage import default_storage
import os
from django.db.utils import OperationalError
from django.contrib.auth.decorators import login_required


def register_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        if form.is_valid():
            # ensure default role exists
            rol, _ = Rol.objects.get_or_create(nom_rol='acudiente')
            registro = form.save(commit=False)
            registro.con_usu = make_password(form.cleaned_data['con_usu'])
            registro.id_rol = rol
            registro.save()
            # create Acudiente with extra fields and uploaded files
            num_doc = form.cleaned_data.get('num_doc_acu')
            tel = form.cleaned_data.get('tel_acu')
            dir_acu = form.cleaned_data.get('dir_acu')
            cedula = request.FILES.get('cedula_img')
            foto = request.FILES.get('foto_perfil')
            Acudiente.objects.create(
                num_doc_acu=num_doc,
                tel_acu=tel,
                dir_acu=dir_acu,
                lat_acu=form.cleaned_data.get('dir_lat'),
                lon_acu=form.cleaned_data.get('dir_lon'),
                acc_acu=form.cleaned_data.get('dir_acc'),
                id_usu=registro,
                cedula_img=cedula,
                foto_perfil=foto,
            )
            request.session['registro_id'] = registro.id_usu
            messages.success(request, 'Registro creado correctamente')
            return redirect(reverse('accounts:dashboard'))
        else:
            # Log de diagnóstico cuando el formulario no es válido
            try:
                if getattr(settings, 'DEBUG', False):
                    import json
                    errs = {k: [str(e) for e in v] for k, v in (form.errors or {}).items()}
                    print('[accounts.register] Form invalid errors:', json.dumps(errs, ensure_ascii=False))
            except Exception:
                pass
    else:
        form = RegistroForm()
    return render(request, 'accounts/register.html', {'form': form})


def address_suggest(request):
    """Endpoint simple para autocompletar direcciones usando Nominatim.

    GET params:
    - q: texto a buscar
    - country: código de país ISO2 (default CO)
    - limit: número de sugerencias (default 5)
    """
    q = (request.GET.get('q') or '').strip()
    # Si no hay q pero sí lat/lon, devolver sugerencias "cercanas"
    lat_param = request.GET.get('lat')
    lon_param = request.GET.get('lon')
    # Normalizar query (bajar a minúsculas y quitar espacios duplicados)
    q_norm = ' '.join(q.lower().split())
    if not q_norm and lat_param and lon_param:
        try:
            import requests
        except Exception:
            return JsonResponse({'results': []})
        try:
            latf = float(lat_param)
            lonf = float(lon_param)
        except Exception:
            return JsonResponse({'results': []})
        # Obtener algunas vías cercanas usando tokens comunes (minimizar llamadas)
        tokens = ['calle', 'carrera']
        resultados = []
        headers = {'User-Agent': 'matrischol/1.0 (admin@matrischol.local)'}
        delta = 0.15
        left = lonf - delta
        right = lonf + delta
        top = latf + delta
        bottom = latf - delta
        for tk in tokens:
            if len(resultados) >= 5:
                break
            params_tok = {
                'q': tk,
                'format': 'jsonv2',
                'addressdetails': 1,
                'limit': 5,
                'viewbox': f"{left},{top},{right},{bottom}",
                'bounded': 1,
                'countrycodes': (request.GET.get('country') or 'CO').strip().lower(),
            }
            try:
                rtk = requests.get('https://nominatim.openstreetmap.org/search', params=params_tok, headers=headers, timeout=4.0)
                rtk.raise_for_status()
                data_tok = rtk.json() or []
            except Exception:
                data_tok = []
            for it in data_tok:
                if len(resultados) >= 5:
                    break
                label = it.get('display_name')
                try:
                    latv = float(it.get('lat')) if it.get('lat') else None
                    lonv = float(it.get('lon')) if it.get('lon') else None
                except Exception:
                    latv = None; lonv = None
                if label and latv is not None and lonv is not None and label not in [r['label'] for r in resultados]:
                    resultados.append({'label': label, 'lat': latv, 'lon': lonv})
        return JsonResponse({'results': resultados})
    if not q_norm:
        return JsonResponse({'results': []})
    country = (request.GET.get('country') or 'CO').strip() or 'CO'
    # Opcional: limitar por lat/lon del usuario (bounding box) para resultados más relevantes
    # lat/lon ya calculados arriba si q vacío; aquí sólo para búsquedas con texto
    lat_param = request.GET.get('lat')
    lon_param = request.GET.get('lon')
    try:
        limit = int(request.GET.get('limit') or '5')
    except Exception:
        limit = 5
    limit = max(1, min(limit, 10))

    try:
        import requests  # importar dentro para no romper en falta de dependencia
    except Exception:
        return JsonResponse({'results': []})

    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': q_norm,
        'format': 'jsonv2',
        'addressdetails': 1,
        'limit': limit,
        'countrycodes': country.lower(),
        'accept-language': 'es',
    }
    if lat_param and lon_param:
        try:
            latf = float(lat_param)
            lonf = float(lon_param)
            delta = 0.15  # ~15km aprox
            left = lonf - delta
            right = lonf + delta
            top = latf + delta
            bottom = latf - delta
            params['viewbox'] = f"{left},{top},{right},{bottom}"
            params['bounded'] = 1
        except Exception:
            pass
    headers = {
        'User-Agent': 'matrischol/1.0 (admin@matrischol.local)'
    }
    def perform_search(local_params):
        try:
            r = requests.get(url, params=local_params, headers=headers, timeout=4.5)
            r.raise_for_status()
            return r.json() or []
        except Exception:
            return []

    data = perform_search(params)
    # Fallback 1: si vacío y query >=3 quitar filtro de país
    if not data and len(q_norm) >= 3:
        params_no_country = dict(params)
        params_no_country.pop('countrycodes', None)
        data = perform_search(params_no_country)
    # Fallback 2: separar tokens y buscar individualmente (merge)
    if not data and len(q_norm) >= 3:
        tokens = [t for t in q_norm.split(' ') if t]
        merged = []
        for tk in tokens:
            p_tok = dict(params)
            p_tok['q'] = tk
            chunk = perform_search(p_tok)
            for it in chunk:
                if it not in merged:
                    merged.append(it)
            if len(merged) >= limit:
                break
        data = merged[:limit]

    results = []
    for it in data:
        try:
            label = it.get('display_name')
            lat = float(it.get('lat')) if it.get('lat') else None
            lon = float(it.get('lon')) if it.get('lon') else None
            if not label or lat is None or lon is None:
                continue
            results.append({'label': label, 'lat': lat, 'lon': lon})
        except Exception:
            continue
    return JsonResponse({'results': results})


def address_reverse(request):
    """Reverse geocoding: lat/lon -> dirección normalizada."""
    try:
        import requests
    except Exception:
        return JsonResponse({'ok': False, 'address': None})
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not lat or not lon:
        return JsonResponse({'ok': False, 'address': None})
    try:
        latf = float(lat)
        lonf = float(lon)
    except Exception:
        return JsonResponse({'ok': False, 'address': None})
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {
        'lat': latf,
        'lon': lonf,
        'format': 'jsonv2',
        'zoom': 20,  # mayor detalle para reverse
        'accept-language': 'es',
    }
    headers = {'User-Agent': 'matrischol/1.0 (admin@matrischol.local)'}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=4.5)
        r.raise_for_status()
        data = r.json() or {}
        display = data.get('display_name')
        return JsonResponse({'ok': bool(display), 'address': display})
    except Exception:
        return JsonResponse({'ok': False, 'address': None})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            pwd = form.cleaned_data['password']
            identifier = email.strip()
            user = None
            # try email first
            try:
                user = Registro.objects.get(ema_usu=identifier)
            except Registro.DoesNotExist:
                user = None
            # if not found by email, try document numbers across related models
            if not user:
                try:
                    acu = Acudiente.objects.filter(num_doc_acu=identifier).select_related('id_usu').first()
                    if acu:
                        user = acu.id_usu
                except Exception:
                    user = None
            if not user:
                try:
                    est = Estudiante.objects.filter(num_doc_est=identifier).select_related('id_usu').first()
                    if est:
                        user = est.id_usu
                except Exception:
                    user = None
            if not user:
                try:
                    adm = Administrativo.objects.filter(num_doc_adm=identifier).select_related('id_usu').first()
                    if adm:
                        user = adm.id_usu
                except Exception:
                    user = None

            if not user:
                messages.error(request, 'No existe una cuenta con ese correo o número de documento')
            elif check_password(pwd, user.con_usu):
                request.session['registro_id'] = user.id_usu
                messages.success(request, 'Sesión iniciada')
                # redirect by role
                rol_name = (user.id_rol.nom_rol or '').lower() if user.id_rol else ''
                if rol_name == 'acudiente':
                    return redirect('accounts:panel_acudiente')
                if rol_name == 'estudiante':
                    return redirect('accounts:panel_estudiante')
                if rol_name == 'administrativo':
                    return redirect('accounts:panel_administrativo')
                if rol_name in ('admin', 'administrator'):
                    return redirect('accounts:panel_admin')
                return redirect(reverse('accounts:dashboard'))
            else:
                messages.error(request, 'Contraseña incorrecta')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    # Remove the entire session to fully invalidate it (clears session cookie/server data)
    request.session.flush()
    messages.info(request, 'Sesión cerrada')
    return redirect(reverse('home'))


def password_reset_request(request):
    """Solicita restablecimiento de contraseña. Respuesta genérica siempre."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                registro = Registro.objects.get(ema_usu=email)
            except Registro.DoesNotExist:
                registro = None
            if registro:
                # invalidar solicitudes anteriores
                PasswordResetRequest.objects.filter(registro=registro, used=False).update(used=True)
                from django.utils import timezone
                from uuid import uuid4
                expires = timezone.now() + timezone.timedelta(minutes=20)
                token = uuid4().hex
                req_obj = PasswordResetRequest.objects.create(
                    registro=registro,
                    token=token,
                    expires_at=expires,
                    ip_request=request.META.get('REMOTE_ADDR')
                )
                try:
                    from communications.email_utils import send_password_reset_email
                    send_password_reset_email(registro, token)
                except Exception:
                    # silencioso: no revelar fallos
                    pass
            messages.info(request, 'Si el correo existe hemos enviado instrucciones para restablecer la contraseña.')
            return redirect('accounts:password_reset_request')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    """Formulario para definir nueva contraseña si token válido."""
    try:
        req_obj = PasswordResetRequest.objects.get(token=token)
    except PasswordResetRequest.DoesNotExist:
        messages.error(request, 'Enlace inválido o expirado')
        return redirect('accounts:password_reset_request')
    if not req_obj.is_valid():
        messages.error(request, 'Enlace inválido o expirado')
        return redirect('accounts:password_reset_request')
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_pwd = form.cleaned_data['new_password']
            req_obj.registro.con_usu = make_password(new_pwd)
            req_obj.registro.save(update_fields=['con_usu'])
            req_obj.mark_used()
            messages.success(request, 'Contraseña restablecida. Inicia sesión con tu nueva contraseña.')
            return redirect('accounts:login')
    else:
        form = PasswordResetConfirmForm()
    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'token': token})


def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html')


def dashboard_view(request):
    user_id = request.session.get('registro_id')
    if not user_id:
        return redirect(reverse('accounts:login'))
    try:
        user = Registro.objects.get(id_usu=user_id)
    except Registro.DoesNotExist:
        return redirect(reverse('accounts:login'))
    # Obtener posibles perfiles vinculados
    acudiente = None
    estudiante = None
    administrativo = None
    instituciones = []
    try:
        acudiente = Acudiente.objects.filter(id_usu=user).first()
    except Exception:
        acudiente = None
    try:
        estudiante = Estudiante.objects.select_related('id_usu', 'id_acu').filter(id_usu=user).first()
    except Exception:
        estudiante = None
    try:
        administrativo = Administrativo.objects.filter(id_usu=user).select_related('id_usu').first()
        if administrativo:
            from school.models import Institucion
            instituciones = list(Institucion.objects.filter(id_adm=administrativo))
    except Exception:
        administrativo = None
        instituciones = []
    return render(request, 'accounts/dashboard.html', {
        'user': user,
        'acudiente': acudiente,
        'estudiante': estudiante,
        'administrativo': administrativo,
        'instituciones': instituciones,
    })


def health_db(request):
    """Endpoint simple para verificar conexión y estado de BD.
    Devuelve motor de BD y conteos básicos.
    """
    from django.db import connection
    engine = settings.DATABASES['default']['ENGINE']
    info = {
        'engine': engine,
        'ok': True,
        'counts': {}
    }
    try:
        info['counts']['Registro'] = Registro.objects.count()
        info['counts']['Rol'] = Rol.objects.count()
        info['counts']['Acudiente'] = Acudiente.objects.count()
    except Exception as e:
        info['ok'] = False
        info['error'] = str(e)
    try:
        with connection.cursor() as cur:
            cur.execute('SELECT 1')
            _ = cur.fetchone()
    except Exception as e:
        info['ok'] = False
        info['error'] = str(e)
    return JsonResponse(info)


def panel_home(request):
    """Redirect to the correct panel depending on the logged-in Registro's role.

    If not logged, redirect to the public home page.
    """
    user_id = request.session.get('registro_id')
    if not user_id:
        return redirect(reverse('home'))
    try:
        user = Registro.objects.get(id_usu=user_id)
    except Registro.DoesNotExist:
        return redirect(reverse('accounts:login'))

    rol_name = (user.id_rol.nom_rol or '').strip().lower() if user.id_rol else ''
    if rol_name == 'acudiente':
        return redirect('accounts:panel_acudiente')
    if rol_name == 'estudiante':
        return redirect('accounts:panel_estudiante')
    if rol_name == 'administrativo':
        return redirect('accounts:panel_administrativo')
    if rol_name in ('admin', 'administrator'):
        return redirect('accounts:panel_admin')
    return redirect(reverse('accounts:dashboard'))


def panel_profile(request):
    """Renderiza el perfil del usuario logeado sin alterar el flujo de login.

    Busca si el registro tiene asociado un Acudiente, Estudiante o Administrativo
    y pasa esos objetos al template `accounts/dashboard.html`.
    """
    reg_id = request.session.get('registro_id')
    if not reg_id:
        return redirect(reverse('accounts:login'))
    try:
        user = Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return redirect(reverse('accounts:login'))

    try:
        acudiente = Acudiente.objects.filter(id_usu=user).first()
    except Exception:
        acudiente = None
    try:
        estudiante = Estudiante.objects.select_related('id_usu', 'id_acu').filter(id_usu=user).first()
    except Exception:
        estudiante = None
    instituciones = []
    try:
        administrativo = Administrativo.objects.filter(id_usu=user).select_related('id_usu').first()
        if administrativo:
            from school.models import Institucion
            instituciones = list(Institucion.objects.filter(id_adm=administrativo))
    except Exception:
        administrativo = None
        instituciones = []

    context = {
        'user': user,
        'acudiente': acudiente,
        'estudiante': estudiante,
        'administrativo': administrativo,
        'instituciones': instituciones,
    }
    return render(request, 'accounts/dashboard.html', context)


def panel_profile(request):
    """Renderiza el panel de perfil del usuario logeado.

    Obtiene el `registro_id` de la sesión y busca si existe un Acudiente,
    Estudiante o Administrativo asociado. Pasa las variables al template
    `accounts/dashboard.html` para que muestre la foto y datos personales.
    """
    reg_id = request.session.get('registro_id')
    if not reg_id:
        return redirect(reverse('accounts:login'))
    try:
        user = Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return redirect(reverse('accounts:login'))

    try:
        acudiente = Acudiente.objects.filter(id_usu=user).first()
    except Exception:
        acudiente = None
    try:
        estudiante = Estudiante.objects.select_related('id_usu', 'id_acu').filter(id_usu=user).first()
    except Exception:
        estudiante = None
    try:
        administrativo = Administrativo.objects.filter(id_usu=user).first()
    except Exception:
        administrativo = None

    context = {
        'user': user,
        'acudiente': acudiente,
        'estudiante': estudiante,
        'administrativo': administrativo,
    }
    return render(request, 'accounts/dashboard.html', context)


def role_required(role_name):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            reg_id = request.session.get('registro_id')
            if not reg_id:
                return redirect('accounts:login')
            try:
                reg = Registro.objects.get(pk=reg_id)
            except Registro.DoesNotExist:
                return redirect('accounts:login')
            actual_role = (reg.id_rol.nom_rol or '').strip().lower() if reg.id_rol else ''
            if not actual_role or actual_role != role_name:
                messages.error(request, 'No tienes permiso para acceder a esta sección')
                return redirect('accounts:panel_home')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


@role_required('acudiente')
def panel_acudiente(request):
    # obtener acudiente y sus estudiantes y calcular estado de documentos
    reg_id = request.session.get('registro_id')
    estudiantes = []
    students_list = []
    try:
        reg = Registro.objects.get(pk=reg_id)
        acu = Acudiente.objects.filter(id_usu=reg).first()
        if acu:
            estudiantes = Estudiante.objects.filter(id_acu=acu).select_related('id_usu')
            for est in estudiantes:
                # Determine required documento fields from the latest matrícula
                from school.models import Matricula, Documento
                missing = []
                # check base Estudiante fields as before
                if not est.fch_nac_estu:
                    missing.append('fecha_nacimiento')
                # El correo es opcional; no marcarlo como documento faltante

                # look for latest matricula and its Documento
                try:
                    mat = Matricula.objects.filter(id_est=est).order_by('-fch_reg_mat').first()
                    doc = None
                    if mat:
                        doc = Documento.objects.filter(id_mat=mat).first()
                    if not doc:
                        doc = Documento.objects.filter(id_est=est).first()
                except OperationalError:
                    # Migration not applied yet (column missing). Fall back to no documento.
                    mat = None
                    doc = None

                # required documento fields (visa_extr_doc es opcional)
                required_doc_fields = [
                    'reg_civil_doc', 'doc_idn_acu', 'doc_idn_alum', 'cnt_vac_doc',
                    'adres_doc', 'fot_alum_doc', 'cer_med_disca_doc', 'cer_esc_doc'
                ]
                for f in required_doc_fields:
                    has = False
                    if doc:
                        val = getattr(doc, f, None)
                        if val:
                            has = True
                    # fallback: some info may be on Estudiante (foto_perfil)
                    if f == 'fot_alum_doc' and est.foto_perfil:
                        has = True
                    if not has:
                        missing.append(f)

                documents_complete = (len(missing) == 0)
                # Determinar grado para visualización (curso asignado o grado solicitado)
                grado_display = None
                try:
                    if mat and getattr(mat, 'id_cur', None) and getattr(mat.id_cur, 'grd_cur', None):
                        grado_display = mat.id_cur.grd_cur
                    elif mat and getattr(mat, 'grado_solicitado', None):
                        grado_display = f"{mat.grado_solicitado}º"
                except Exception:
                    grado_display = None
                students_list.append({
                    'est': est,
                    'documents_complete': documents_complete,
                    'missing': missing,
                    'documento': doc,
                    'matricula': mat,
                    'grado_display': grado_display,
                })
    except Exception:
        students_list = []
    # añadimos acudiente a contexto para dashboard y para el modal
    try:
        acudiente = Acudiente.objects.filter(id_usu=reg).first()
    except Exception:
        acudiente = None
    # Instituciones sugeridas (hasta 6 aleatorias) con sus cursos para grados ofrecidos
    from school.models import Institucion, Curso
    try:
        # Obtener hasta 6 instituciones aleatorias
        suggested_instituciones = list(Institucion.objects.order_by('?')[:6])
        import random
        # Duplicar si hay menos de 6 para completar siempre dos páginas de 3
        if suggested_instituciones and len(suggested_instituciones) < 6:
            base = suggested_instituciones[:]
            while len(suggested_instituciones) < 6:
                suggested_instituciones.append(random.choice(base))
        # Prefetch cursos para evitar múltiples queries en template
        inst_ids = [i.id_inst for i in suggested_instituciones]
        # Calcular número de páginas del carrusel (grupos de 3)
        import math
        carousel_pages = math.ceil(len(suggested_instituciones) / 3) if suggested_instituciones else 0
        carousel_range = range(carousel_pages)
        cursos_map = {}
        for c in Curso.objects.filter(id_inst__in=inst_ids):
            cursos_map.setdefault(c.id_inst_id, []).append(c)
        # Adjuntar lista de cursos al objeto (atributo dinámico)
        for i in suggested_instituciones:
            setattr(i, 'cursos_list', cursos_map.get(i.id_inst, []))
    except Exception:
        suggested_instituciones = []
        carousel_pages = 0
        carousel_range = range(0)
    return render(request, 'accounts/panels/acudiente.html', {
        'students_list': students_list,
        'acudiente': acudiente,
        'suggested_instituciones': suggested_instituciones,
        'carousel_pages': carousel_pages,
        'carousel_range': carousel_range,
    })


def upload_profile_photo(request):
    """Permite al usuario subir o actualizar su foto de perfil desde el dashboard.

    Acepta Acudiente, Estudiante o Administrativo según el registro autenticado
    y guarda la imagen en el campo `foto_perfil` del modelo correspondiente.
    """
    if request.method != 'POST':
        return redirect('accounts:panel_home')
    reg_id = request.session.get('registro_id')
    if not reg_id:
        return redirect('accounts:login')
    try:
        reg = Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return redirect('accounts:login')

    # Try to find the profile object for each role
    acu = Acudiente.objects.filter(id_usu=reg).first()
    adm = Administrativo.objects.filter(id_usu=reg).first()
    est = Estudiante.objects.filter(id_usu=reg).first()

    profile_obj = None
    if acu:
        profile_obj = acu
    elif adm:
        profile_obj = adm
    elif est:
        profile_obj = est

    if not profile_obj:
        messages.error(request, 'No se encontró un perfil asociado a la cuenta.')
        return redirect('accounts:panel_home')

    f = request.FILES.get('foto_perfil')
    if not f:
        messages.error(request, 'No se seleccionó ninguna imagen.')
        return redirect('accounts:panel_home')

    # Simple validation
    content_type = getattr(f, 'content_type', '')
    if not content_type.startswith('image/'):
        messages.error(request, 'El archivo debe ser una imagen.')
        return redirect('accounts:panel_home')
    if f.size and f.size > 5 * 1024 * 1024:
        messages.error(request, 'La imagen debe ser menor a 5 MB.')
        return redirect('accounts:panel_home')

    # Save and redirect back
    try:
        profile_obj.foto_perfil = f
        profile_obj.save()
        messages.success(request, 'Foto de perfil actualizada correctamente.')
    except Exception:
        messages.error(request, 'Ocurrió un error al guardar la imagen.')
    # Redirect to panel_home so the user lands on their role-specific panel
    return redirect('accounts:panel_home')

def update_profile_details(request):
    """Actualiza nombre del usuario y teléfono/dirección del perfil asociado.

    Acepta POST con: nom_usu, ape_usu, tel, dir, foto_perfil (opcional).
    Si el usuario tiene Acudiente vinculado, actualiza tel_acu y dir_acu.
    Si tiene Estudiante, actualiza tel_est y dir_est.
    Responde JSON para uso desde modal en la misma página.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Método no permitido'}, status=405)
    try:
        reg = None
        # Preferimos la sesión usada en todo el sitio
        reg_id = request.session.get('registro_id')
        if reg_id:
            try:
                reg = Registro.objects.get(pk=reg_id)
            except Registro.DoesNotExist:
                reg = None
        if not reg:
            reg = request.user if hasattr(request, 'user') else None
        if not reg:
            return JsonResponse({'status': 'error', 'error': 'No autenticado'}, status=401)

        nom = (request.POST.get('nom_usu') or '').strip()
        ape = (request.POST.get('ape_usu') or '').strip()
        tel = (request.POST.get('tel') or '').strip()
        dire = (request.POST.get('dir') or '').strip()
        foto = request.FILES.get('foto_perfil')

        changed = False
        if nom:
            reg.nom_usu = nom
            changed = True
        if ape:
            reg.ape_usu = ape
            changed = True
        if changed:
            reg.save(update_fields=['nom_usu', 'ape_usu'])

        # Actualizar perfil vinculado
        updated_model = None
        try:
            acu = Acudiente.objects.filter(id_usu=reg).first()
        except Exception:
            acu = None
        try:
            est = Estudiante.objects.filter(id_usu=reg).first()
        except Exception:
            est = None
        try:
            adm = Administrativo.objects.filter(id_usu=reg).first()
        except Exception:
            adm = None

        if acu:
            if tel:
                acu.tel_acu = tel
                changed = True
            if dire:
                acu.dir_acu = dire
                changed = True
            if foto:
                acu.foto_perfil = foto
                changed = True
            acu.save()
            updated_model = 'acudiente'
        elif est:
            if tel:
                # En modelo Estudiante el campo es tel_estu
                est.tel_estu = tel
                changed = True
            if dire:
                # Estudiante puede no tener dir_est; intentar setear si existe
                if hasattr(est, 'dir_est'):
                    est.dir_est = dire
                    changed = True
            if foto:
                est.foto_perfil = foto
                changed = True
            est.save()
            updated_model = 'estudiante'
        elif adm:
            if tel:
                adm.tel_adm = tel
                changed = True
            if dire:
                adm.dir_adm = dire
                changed = True
            if foto:
                adm.foto_perfil = foto
                changed = True
            adm.save()
            updated_model = 'administrativo'

        avatar_url = None
        try:
            if acu and acu.foto_perfil:
                avatar_url = acu.foto_perfil.url
            elif est and est.foto_perfil:
                avatar_url = est.foto_perfil.url
            elif adm and adm.foto_perfil:
                avatar_url = adm.foto_perfil.url
        except Exception:
            avatar_url = None

        return JsonResponse({'status': 'ok', 'updated': bool(changed), 'profile': updated_model, 'avatar': avatar_url})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@role_required('acudiente')
def estudiante_detail(request, pk):
    # Mostrar datos de un estudiante perteneciente al acudiente
    reg_id = request.session.get('registro_id')
    try:
        reg = Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return redirect('accounts:login')
    try:
        acu = Acudiente.objects.filter(id_usu=reg).first()
    except Exception:
        acu = None

    estudiante = None
    try:
        estudiante = Estudiante.objects.select_related('id_usu', 'id_acu').get(pk=pk)
    except Estudiante.DoesNotExist:
        estudiante = None

    # handle uploads for foto_perfil and Documento fields from this detail view
    from school.models import Matricula, Documento
    from school.forms import DocumentoUploadForm

    try:
        # find latest matricula and documento (prefer documento linked to matricula, fallback to documento linked to estudiante)
        mat = Matricula.objects.filter(id_est=estudiante).order_by('-fch_reg_mat').first() if estudiante else None
        documento = None
        if mat:
            documento = Documento.objects.filter(id_mat=mat).first()
        if not documento and estudiante:
            documento = Documento.objects.filter(id_est=estudiante).first()
    except OperationalError:
        # DB schema not updated yet; avoid crash and show no documento
        mat = None
        documento = None

    # POST handling: foto_perfil or documento uploads
    if request.method == 'POST' and estudiante:
        # foto_perfil upload (keeps existing behavior)
        foto = request.FILES.get('foto_perfil')
        if foto:
            estudiante.foto_perfil = foto
            estudiante.save()
            messages.success(request, 'Foto del estudiante subida correctamente')
            return redirect('accounts:estudiante_detail', pk=pk)

        # documento uploads
        form = DocumentoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = form.files_present()
            if files:
                # create documento row if none exists; prefer linking to matricula when available
                if not documento:
                    documento = Documento.objects.create(id_mat=mat if mat else None, id_est=estudiante)

                for field_name, uploaded in files.items():
                    base_dir = os.path.join('documentos', str(estudiante.id_est))
                    filename = uploaded.name
                    dest_name = os.path.join(base_dir, f"{field_name}_{filename}")
                    saved_path = default_storage.save(dest_name, uploaded)
                    # normalize to forward slashes for URLs
                    saved_path = saved_path.replace(os.sep, '/') if os.sep != '/' else saved_path
                    setattr(documento, field_name, saved_path)
                documento.save()
                # enviar notificación por email al acudiente indicando que los documentos fueron subidos
                try:
                    from communications.email_utils import send_documents_uploaded_email
                    # preparar lista de campos subidos para el correo (etiqueta amigable + nombre de archivo)
                    uploaded_fields = []
                    if isinstance(files, dict):
                        for fname, uploaded in files.items():
                            label = None
                            try:
                                label = form.fields[fname].label
                            except Exception:
                                label = fname
                            filename = getattr(uploaded, 'name', str(uploaded))
                            uploaded_fields.append(f"{label}: {filename}")
                    estudiante_nombre = f"{estudiante.id_usu.nom_usu} {estudiante.id_usu.ape_usu}"
                    send_documents_uploaded_email(reg, estudiante_nombre, uploaded_fields)
                except Exception:
                    pass
                messages.success(request, 'Documentos subidos correctamente')
                return redirect('accounts:estudiante_detail', pk=pk)

    # deny access if the student doesn't belong to this acudiente
    if not estudiante or (acu and estudiante.id_acu != acu):
        # show panel with error message
        from django.contrib import messages
        messages.error(request, 'No tienes permiso para ver ese estudiante o no existe.')
        return redirect('accounts:panel_acudiente')

    # compute documento completeness for template (visa_extr_doc es opcional)
    required_doc_fields = [
        'reg_civil_doc', 'doc_idn_acu', 'doc_idn_alum', 'cnt_vac_doc',
        'adres_doc', 'fot_alum_doc', 'cer_med_disca_doc', 'cer_esc_doc'
    ]
    missing_docs = []
    for f in required_doc_fields:
        has = False
        if documento and getattr(documento, f):
            has = True
        if f == 'fot_alum_doc' and estudiante.foto_perfil:
            has = True
        if not has:
            missing_docs.append(f)

    # determine 'major' documents completeness: at least 5 important docs
    important_fields = ['reg_civil_doc', 'doc_idn_alum', 'fot_alum_doc', 'cnt_vac_doc', 'doc_idn_acu']
    major_count = 0
    for f in important_fields:
        ok = False
        if documento and getattr(documento, f):
            ok = True
        if f == 'fot_alum_doc' and estudiante.foto_perfil:
            ok = True
        if ok:
            major_count += 1
    major_complete = (major_count >= 5)

    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    # otros estudiantes del mismo acudiente (hermanos)
    siblings = []
    siblings_info = []
    try:
        if acu:
            siblings = list(Estudiante.objects.select_related('id_usu').filter(id_acu=acu).exclude(pk=estudiante.pk))
            # Obtener institución y grado para cada herman@ (última matrícula)
            from school.models import Matricula
            for s in siblings:
                inst_name = None
                grado_disp = None
                try:
                    smat = Matricula.objects.filter(id_est=s).select_related('id_cur__id_inst').order_by('-fch_reg_mat').first()
                    if smat and getattr(smat, 'id_cur', None):
                        if getattr(smat.id_cur, 'id_inst', None):
                            inst_name = smat.id_cur.id_inst.nom_inst
                        if getattr(smat.id_cur, 'grd_cur', None):
                            grado_disp = smat.id_cur.grd_cur
                    # si no hay curso asignado, mostrar grado solicitado si existe
                    if not grado_disp and smat and getattr(smat, 'grado_solicitado', None):
                        grado_disp = smat.grado_solicitado
                except Exception:
                    inst_name = None
                    grado_disp = None
                siblings_info.append({
                    's': s,
                    'inst': inst_name,
                    'grado': grado_disp,
                })
    except Exception:
        siblings = []
        siblings_info = []

    return render(request, 'accounts/estudiante_detail.html', {
        'est': estudiante,
        'documento': documento,
        'matricula': mat,
        'missing_docs': missing_docs,
        'media_url': media_url,
        'major_count': major_count,
        'major_complete': major_complete,
        'siblings': siblings,
        'siblings_info': siblings_info,
    })


@role_required('acudiente')
def documentos_panel(request, pk):
    """Panel para subir y revisar documentos vinculados a la matrícula del estudiante."""
    from school.models import Matricula, Documento
    from school.forms import DocumentoUploadForm

    reg_id = request.session.get('registro_id')
    try:
        reg = Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return redirect('accounts:login')
    acu = Acudiente.objects.filter(id_usu=reg).first()

    try:
        estudiante = Estudiante.objects.select_related('id_usu', 'id_acu').get(pk=pk)
    except Estudiante.DoesNotExist:
        messages.error(request, 'Estudiante no encontrado')
        return redirect('accounts:panel_acudiente')

    if estudiante.id_acu != acu:
        messages.error(request, 'No tienes permiso para gestionar documentos de ese estudiante')
        return redirect('accounts:panel_acudiente')

    try:
        # buscar la matrícula más reciente
        mat = Matricula.objects.filter(id_est=estudiante).order_by('-fch_reg_mat').first()
        documento = None
        if mat:
            documento = Documento.objects.filter(id_mat=mat).first()
        # si no encontramos documento ligado a la matrícula, buscar por estudiante
        if not documento:
            documento = Documento.objects.filter(id_est=estudiante).first()
    except OperationalError:
        mat = None
        documento = None

    if request.method == 'POST':
        form = DocumentoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = form.files_present()
            adres_text = form.cleaned_data.get('adres_text')
            # Accept either uploaded files or a textual address (or both)
            if files or adres_text:
                # create documento row if none exists; link to matricula when available otherwise to estudiante
                if not documento:
                    documento = Documento.objects.create(id_mat=mat if mat else None, id_est=estudiante)
                # save uploaded files
                for field_name, uploaded in files.items():
                    base_dir = os.path.join('documentos', str(estudiante.id_est))
                    filename = uploaded.name
                    dest_name = os.path.join(base_dir, f"{field_name}_{filename}")
                    saved_path = default_storage.save(dest_name, uploaded)
                    # normalize to forward slashes for URLs
                    saved_path = saved_path.replace(os.sep, '/') if os.sep != '/' else saved_path
                    setattr(documento, field_name, saved_path)
                # if an address text was provided and no address file was uploaded, save the text
                if adres_text:
                    if not files.get('adres_doc'):
                        documento.adres_doc = adres_text
                documento.save()
                # enviar notificación por email al acudiente indicando que los documentos fueron subidos
                try:
                    from communications.email_utils import send_documents_uploaded_email
                    uploaded_fields = []
                    if isinstance(files, dict):
                        for fname, uploaded in files.items():
                            label = None
                            try:
                                label = form.fields[fname].label
                            except Exception:
                                label = fname
                            filename = getattr(uploaded, 'name', str(uploaded))
                            uploaded_fields.append(f"{label}: {filename}")
                    estudiante_nombre = f"{estudiante.id_usu.nom_usu} {estudiante.id_usu.ape_usu}"
                    send_documents_uploaded_email(reg, estudiante_nombre, uploaded_fields)
                except Exception:
                    pass
                messages.success(request, 'Documentos subidos correctamente')
                return redirect('accounts:documentos_panel', pk=pk)
            else:
                messages.error(request, 'No se seleccionaron archivos ni se proporcionó dirección. Selecciona un archivo o escribe la dirección.')
                return redirect('accounts:documentos_panel', pk=pk)
    else:
        form = DocumentoUploadForm()

    # determinar estado (visa_extr_doc es opcional)
    required = [
        'reg_civil_doc', 'doc_idn_acu', 'doc_idn_alum', 'cnt_vac_doc',
        'adres_doc', 'fot_alum_doc', 'cer_med_disca_doc', 'cer_esc_doc'
    ]
    missing = []
    for f in required:
        ok = False
        if documento and getattr(documento, f):
            ok = True
        if f == 'fot_alum_doc' and estudiante.foto_perfil:
            ok = True
        if not ok:
            missing.append(f)

    documents_complete = (len(missing) == 0)
    media_url = getattr(settings, 'MEDIA_URL', '/media/')

    return render(request, 'accounts/documentos_panel.html', {'est': estudiante, 'mat': mat, 'documento': documento, 'form': form, 'missing': missing, 'documents_complete': documents_complete, 'media_url': media_url})


@role_required('acudiente')
def register_student(request):
    from .forms import StudentRegistrationForm
    from django.contrib.auth.hashers import make_password
    from people.models import Estudiante, Acudiente
    from accounts.models import Registro, Rol

    # get current acudiente record
    reg = None
    try:
        reg_id = request.session.get('registro_id')
        reg = Registro.objects.get(pk=reg_id)
    except Exception:
        reg = None

    try:
        acu = Acudiente.objects.filter(id_usu=reg).first()
    except Exception:
        acu = None

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            # ensure student role exists
            rol, _ = Rol.objects.get_or_create(nom_rol='estudiante')
            email = data.get('ema_usu')
            if not email:
                # generate system email to avoid nulls
                email = f"student+{data.get('num_doc_est')}@noemail.local"

            # ensure unique email; if collision, append random suffix
            from django.db import IntegrityError
            import random
            original_email = email
            attempts = 0
            while Registro.objects.filter(ema_usu=email).exists() and attempts < 5:
                attempts += 1
                local, at, domain = original_email.partition('@')
                email = f"{local}+{random.randint(1000,9999)}@{domain or 'noemail.local'}"

            try:
                registro = Registro.objects.create(
                    nom_usu=data.get('nom_usu'),
                    ape_usu=data.get('ape_usu'),
                    ema_usu=email,
                    con_usu=make_password(data.get('con_usu')),
                    id_rol=rol
                )
                est = Estudiante.objects.create(
                    tip_doc_est='CC',
                    num_doc_est=data.get('num_doc_est'),
                    fch_nac_estu=data.get('fch_nac_estu'),
                    tel_estu=data.get('tel_estu'),
                    id_usu=registro,
                    id_acu=acu,
                    foto_perfil=request.FILES.get('foto_perfil')
                )
            except IntegrityError as e:
                messages.error(request, 'No se pudo crear el estudiante: datos duplicados o error en la base de datos.')
                form.add_error(None, 'Error interno al crear el registro. Intenta con otros datos.')
            except Exception as e:
                messages.error(request, 'Ocurrió un error al crear el estudiante.')
                form.add_error(None, 'Error interno: ' + str(e))
            else:
                # Enviar email de confirmación al acudiente
                try:
                    from communications.email_utils import send_student_registration_email
                    estudiante_nombre = f"{registro.nom_usu} {registro.ape_usu}"
                    send_student_registration_email(reg, estudiante_nombre, data.get('num_doc_est'))
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error enviando email registro estudiante: {e}")
                messages.success(request, 'Estudiante registrado correctamente')
                return redirect('accounts:panel_acudiente')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register_student.html', {'form': form, 'acudiente': acu})


@role_required('estudiante')
def panel_estudiante(request):
    # Mostrar el perfil del estudiante dentro del `dashboard.html` para un UX consistente
    reg_id = request.session.get('registro_id')
    if not reg_id:
        return redirect('accounts:login')
    try:
        user = Registro.objects.get(pk=reg_id)
    except Registro.DoesNotExist:
        return redirect('accounts:login')
    try:
        estudiante = Estudiante.objects.select_related('id_usu', 'id_acu').filter(id_usu=user).first()
    except Exception:
        estudiante = None
    # attempt to fetch latest matrícula and the linked institución (if exists)
    matricula = None
    institucion = None
    try:
        from school.models import Matricula
        # prefer latest matricula and follow relations to curso -> institucion
        matricula = Matricula.objects.filter(id_est=estudiante).select_related('id_cur__id_inst').order_by('-fch_reg_mat').first() if estudiante else None
        if matricula and getattr(matricula, 'id_cur', None) and getattr(matricula.id_cur, 'id_inst', None):
            institucion = matricula.id_cur.id_inst
    except Exception:
        matricula = None
        institucion = None

    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    # load horarios for the enrolled course (if any) and prepare slot rows
    slots = []
    try:
        from school.models import Horario
        curso = getattr(matricula, 'id_cur', None) if matricula else None
        horarios_qs = Horario.objects.filter(id_cur=curso).select_related('id_asig').order_by('hora_inicio', 'dia') if curso else Horario.objects.none()
        # collect unique time slots in order
        slot_keys = []
        for h in horarios_qs:
            key = (h.hora_inicio, h.hora_fin)
            if key not in slot_keys:
                slot_keys.append(key)
        # build slot rows with day cells (0..4)
        for key in slot_keys:
            row = {'start': key[0], 'end': key[1], 'cells': {0: None, 1: None, 2: None, 3: None, 4: None}}
            slots.append(row)
        # populate cells
        for h in horarios_qs:
            key = (h.hora_inicio, h.hora_fin)
            try:
                idx = slot_keys.index(key)
                slots[idx]['cells'][h.dia] = h
            except ValueError:
                # ignore unexpected
                pass
        # create ordered list per slot for easy template iteration (L-V)
        for slot in slots:
            slot['cells_list'] = [slot['cells'].get(i) for i in range(5)]
        # assign a pastel color per time slot (palette is customizable here)
        palette = ['#FDECEC', '#E8F8F5', '#FFF5E6', '#F3E8FF', '#E8F0FF', '#E8FFE8']
        def _hex_to_rgb(hexc):
            h = hexc.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        def _brightness(rgb):
            r, g, b = rgb
            return 0.299 * r + 0.587 * g + 0.114 * b
        for idx, slot in enumerate(slots):
            color = palette[idx % len(palette)]
            slot['bg_color'] = color
            rgb = _hex_to_rgb(color)
            slot['text_color'] = '#ffffff' if _brightness(rgb) < 150 else '#111827'
    except Exception:
        slots = []

    return render(request, 'accounts/panels/estudiante.html', {
        'user': user,
        'estudiante': estudiante,
        'matricula': matricula,
        'institucion': institucion,
        'curso': getattr(matricula, 'id_cur', None),
        'media_url': media_url,
        'slots': slots,
    })


@role_required('administrativo')
def panel_administrativo(request):
    # show linked institutions and notifications for administrativos
    reg_id = request.session.get('registro_id')
    instituciones = []
    notifications_count = 0
    user = None
    try:
        reg = Registro.objects.get(pk=reg_id)
        user = reg
        adm = Administrativo.objects.filter(id_usu=reg).select_related('id_usu').first()
        if adm:
            from school.models import Institucion
            instituciones = Institucion.objects.filter(id_adm=adm)
        # import admin notifications lazily
        try:
            from adminpanel.models import AdminNotification
            notifications_count = AdminNotification.objects.filter(user=reg, is_read=False).count()
        except Exception:
            notifications_count = 0
    except Registro.DoesNotExist:
        pass
    return render(request, 'accounts/panels/administrativo.html', {'user': user, 'instituciones': instituciones, 'notifications_count': notifications_count})


@role_required('admin')
def panel_admin(request):
    return render(request, 'accounts/panels/admin.html')
