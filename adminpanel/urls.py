from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('registros/', views.registro_list, name='registro_list'),
    path('registros/create/', views.registro_create, name='registro_create'),
    path('registros/<int:pk>/edit/', views.registro_edit, name='registro_edit'),
    path('registros/<int:pk>/delete/', views.registro_delete, name='registro_delete'),
    path('registros/<int:pk>/password/', views.registro_change_password, name='registro_change_password'),
    # Rol management
    path('roles/', views.rol_list, name='rol_list'),
    path('roles/create/', views.rol_create, name='rol_create'),
    path('roles/<int:pk>/edit/', views.rol_edit, name='rol_edit'),
    path('roles/<int:pk>/delete/', views.rol_delete, name='rol_delete'),
    # Instituciones
    path('instituciones/', views.institucion_list, name='institucion_list'),
    path('instituciones/create/', views.institucion_create, name='institucion_create'),
    path('instituciones/<int:pk>/edit/', views.institucion_edit, name='institucion_edit'),
    path('instituciones/<int:pk>/delete/', views.institucion_delete, name='institucion_delete'),
    path('instituciones/<int:pk>/bulk_cursos/', views.institucion_bulk_cursos, name='institucion_bulk_cursos'),
    path('instituciones/<int:pk>/clear_cursos/', views.institucion_clear_cursos, name='institucion_clear_cursos'),
    path('instituciones/<int:pk>/cursos/', views.curso_list_by_institucion, name='institucion_curso_list'),
    path('instituciones/<int:pk>/maestros/', views.institucion_maestros, name='institucion_maestros'),
    path('maestros/<int:pk>/edit/', views.maestro_edit, name='maestro_edit'),
    path('maestros/<int:pk>/delete/', views.maestro_delete, name='maestro_delete'),
    # Cursos
    path('cursos/', views.curso_list, name='curso_list'),
    path('cursos/<int:pk>/matriculas/', views.curso_matriculas, name='curso_matriculas'),
    path('cursos/<int:pk>/horario/', views.curso_horario, name='curso_horario'),
    path('cursos/export/csv/', views.curso_export_csv, name='curso_export_csv'),
    path('cursos/create/', views.curso_create, name='curso_create'),
    path('cursos/<int:pk>/edit/', views.curso_edit, name='curso_edit'),
    path('cursos/<int:pk>/delete/', views.curso_delete, name='curso_delete'),
    # Administrativos
    path('administrativos/', views.administrativo_list, name='administrativo_list'),
    path('administrativos/create/', views.administrativo_create, name='administrativo_create'),
    path('administrativos/<int:pk>/edit/', views.administrativo_edit, name='administrativo_edit'),
    path('administrativos/<int:pk>/delete/', views.administrativo_delete, name='administrativo_delete'),
    # Exports
    path('registros/export/csv/', views.registro_export_csv, name='registro_export_csv'),
    # Audit logs
    path('logs/', views.admin_logs, name='admin_logs'),
    # Administrative institution flows
    path('my/instituciones/', views.my_instituciones, name='my_instituciones'),
    path('my/instituciones/solicitar/', views.request_institucion_create, name='request_institucion_create'),
    path('my/instituciones/<int:pk>/solicitar_cursos/', views.request_curso_create, name='request_curso_create'),
    path('solicitudes/instituciones/', views.administracion_institucion_requests, name='administracion_institucion_requests'),
    path('solicitudes/instituciones/<int:pk>/', views.administracion_institucion_request_detail, name='administracion_institucion_request_detail'),
    path('solicitudes/cursos/', views.administracion_curso_requests, name='administracion_curso_requests'),
    path('solicitudes/cursos/<int:pk>/', views.administracion_curso_request_detail, name='administracion_curso_request_detail'),
    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/mark_read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark_all/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    # public view for request details (submitter view)
    path('solicitudes/instituciones/public/<int:pk>/', views.institucion_request_public_view, name='institucion_request_public'),
    path('solicitudes/cursos/public/<int:pk>/', views.curso_request_public_view, name='curso_request_public'),
    # Matricula requests
    path('solicitudes/matriculas/<int:pk>/', views.matricula_request_detail, name='matricula_request_detail'),
]
