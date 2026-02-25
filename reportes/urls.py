from django.urls import path
from . import views

urlpatterns = [
    path('reportes/',        views.reporte_lista,   name='reporte_lista'),
    path('reportes/excel/',  views.exportar_excel,  name='exportar_excel'),
]