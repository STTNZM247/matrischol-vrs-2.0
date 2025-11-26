from django.contrib import admin
from django.utils.html import format_html
from .models import Rol, Registro, Administrativo


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'nom_rol')


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('id_usu', 'nom_usu', 'ape_usu', 'ema_usu', 'id_rol', 'is_password_hashed')
    search_fields = ('nom_usu', 'ape_usu', 'ema_usu')
    readonly_fields = ('con_usu','hashed_password')
    fieldsets = (
        (None, {
            'fields': ('nom_usu', 'ape_usu', 'ema_usu', 'id_rol', 'con_usu', 'hashed_password')
        }),
    )

    def is_password_hashed(self, obj):
        val = (obj.con_usu or '')
        # Common Django hasher prefixes: 'pbkdf2_', 'argon2', 'bcrypt', 'sha1$' etc
        prefixes = ['pbkdf2_', 'argon2', 'bcrypt', 'bcrypt_sha256', 'sha1$', 'md5$']
        return any(val.startswith(p) or ('$' in val and val.split('$', 1)[0] in ['pbkdf2_sha256','pbkdf2_sha1','argon2']) for p in prefixes)
    is_password_hashed.boolean = True
    is_password_hashed.short_description = 'Password hashed'

    def hashed_password(self, obj):
        # show raw hash in monospaced block for inspection
        if not obj or not obj.con_usu:
            return '-'
        return format_html('<pre style="font-family:monospace; font-size:0.9rem; margin:0">{}</pre>', obj.con_usu)
    hashed_password.short_description = 'Hashed password (raw)'


@admin.register(Administrativo)
class AdministrativoAdmin(admin.ModelAdmin):
    list_display = ('id_adm', 'num_doc_adm', 'id_usu')
