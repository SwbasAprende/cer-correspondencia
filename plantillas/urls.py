from django.urls import path
from . import views

urlpatterns = [
    path('plantillas/',                          views.plantilla_lista,        name='plantilla_lista'),
    path('plantillas/<str:tipo>/editar/',        views.plantilla_editar,       name='plantilla_editar'),
    path('plantillas/generar/<int:documento_pk>/', views.generar_documento_pdf, name='generar_pdf'),
    path('plantillas/descargar/<int:pk>/',       views.descargar_pdf,          name='descargar_pdf'),
]