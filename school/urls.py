from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('search/', views.institutions_search, name='institutions_search'),
    path('request/create/', views.matricula_request_create, name='matricula_request_create'),
    path('course/schedule/<int:course_id>/', views.course_schedule, name='course_schedule'),
]
