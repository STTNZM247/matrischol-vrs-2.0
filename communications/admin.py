from django.contrib import admin
from .models import Mensaje, Notificacion, Reporte


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('id_men', 'id_remitente', 'id_destinatario', 'fch_envio', 'leido')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id_notif', 'tit_notif', 'id_usu', 'fch_envio', 'leida')


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('id_rep', 'tit_rep', 'id_usu', 'fch_rep')
