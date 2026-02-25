from django.urls import path
from . import views

urlpatterns = [
    path('documentos/',              views.documento_lista,  name='documento_lista'),
    path('documentos/nuevo/',        views.documento_nuevo,  name='documento_nuevo'),
    path('documentos/<int:pk>/',     views.documento_detalle, name='documento_detalle'),
    path('documentos/<int:pk>/editar/', views.documento_editar, name='documento_editar'),
]