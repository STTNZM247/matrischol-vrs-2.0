from django.contrib import admin
from .models import Acudiente, Estudiante


@admin.register(Acudiente)
class AcudienteAdmin(admin.ModelAdmin):
    list_display = ('id_acu', 'num_doc_acu', 'id_usu')


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('id_est', 'num_doc_est', 'id_usu', 'id_acu')
