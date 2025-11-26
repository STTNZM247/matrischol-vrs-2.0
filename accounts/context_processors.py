from .models import Registro
try:
    from adminpanel.models import AdminActionLog
except Exception:
    AdminActionLog = None
try:
    from adminpanel.models import AdminNotification
except Exception:
    AdminNotification = None
try:
    from people.models import Acudiente, Estudiante
except Exception:
    Acudiente = None
    Estudiante = None
try:
    from .models import Administrativo
except Exception:
    Administrativo = None


def current_registro(request):
    """Context processor que expone el `Registro` actualmente logueado en las plantillas.

    Devuelve {'current_registro': Registro instance} o {} si no hay sesión activa.
    """
    reg_id = request.session.get('registro_id')
    if not reg_id:
        return {}
    try:
        reg = Registro.objects.select_related('id_rol').get(id_usu=reg_id)
        # defaults to avoid template errors when audit table is missing or user is not admin
        context = {'current_registro': reg, 'recent_admin_actions': [], 'recent_admin_actions_count': 0}
        # if admin, expose recent actions for notification UI
        try:
            if AdminActionLog and reg.id_rol and (reg.id_rol.nom_rol or '').lower() in ('admin', 'administrator'):
                # Force evaluation inside the try/except to avoid lazy QuerySet DB access from templates
                recent_qs = AdminActionLog.objects.all().order_by('-timestamp')[:6]
                try:
                    recent_list = list(recent_qs)
                except Exception:
                    recent_list = []
                context['recent_admin_actions'] = recent_list
                context['recent_admin_actions_count'] = len(recent_list)
        except Exception:
            context['recent_admin_actions'] = []
            context['recent_admin_actions_count'] = 0

        # unread notifications for any user (safe)
        try:
            if AdminNotification:
                try:
                    unread = AdminNotification.objects.filter(user=reg, is_read=False).count()
                except Exception:
                    unread = 0
                context['unread_notifications_count'] = unread
        except Exception:
            context['unread_notifications_count'] = 0
        # ensure unread_notifications_count key exists
        if 'unread_notifications_count' not in context:
            context['unread_notifications_count'] = 0
        # determine header avatar (search through role objects)
        avatar_url = None
        initials = ''
        try:
            if Acudiente:
                acu = Acudiente.objects.filter(id_usu=reg).first()
                if acu and getattr(acu, 'foto_perfil', None):
                    avatar_url = getattr(acu.foto_perfil, 'url', None)
            if not avatar_url and Estudiante:
                est = Estudiante.objects.select_related('id_usu').filter(id_usu=reg).first()
                if est and getattr(est, 'foto_perfil', None):
                    avatar_url = getattr(est.foto_perfil, 'url', None)
            if not avatar_url and Administrativo:
                adm = Administrativo.objects.filter(id_usu=reg).first()
                if adm and getattr(adm, 'foto_perfil', None):
                    avatar_url = getattr(adm.foto_perfil, 'url', None)
        except Exception:
            avatar_url = None
        try:
            initials = (reg.nom_usu or '')[:1] + (reg.ape_usu or '')[:1]
        except Exception:
            initials = ''
        context['header_avatar_url'] = avatar_url
        context['header_avatar_initials'] = initials
        return context
    except Registro.DoesNotExist:
        return {}
