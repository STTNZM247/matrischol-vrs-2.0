from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('address/suggest/', views.address_suggest, name='address_suggest'),
    path('address/reverse/', views.address_reverse, name='address_reverse'),
    path('forgot/', views.password_reset_request, name='password_reset_request'),
    path('reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_done, name='password_reset_done'),
    path('panel/', views.panel_home, name='panel_home'),
    path('panel/profile/', views.panel_profile, name='panel_profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('panel/acudiente/', views.panel_acudiente, name='panel_acudiente'),
    path('panel/acudiente/registrar_estudiante/', views.register_student, name='register_student'),
    path('panel/acudiente/estudiante/<int:pk>/', views.estudiante_detail, name='estudiante_detail'),
    path('panel/acudiente/documentos/<int:pk>/', views.documentos_panel, name='documentos_panel'),
    path('panel/acudiente/upload_foto/', views.upload_profile_photo, name='upload_profile_photo'),
    path('panel/update_profile_details/', views.update_profile_details, name='update_profile_details'),
    path('panel/estudiante/', views.panel_estudiante, name='panel_estudiante'),
    path('panel/administrativo/', views.panel_administrativo, name='panel_administrativo'),
    path('panel/admin/', views.panel_admin, name='panel_admin'),
]
