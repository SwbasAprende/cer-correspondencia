from django.urls import path
from . import views

urlpatterns = [
    path('plantillas/', views.plantilla_lista, name='plantilla_lista'),
]