from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('login/',    LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/',   LogoutView.as_view(), name='logout'),
    path('sin-permisos/', views.sin_permisos, name='sin_permisos'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('usuarios/', views.usuario_lista, name='usuario_lista'),
    path('perfil/',            views.perfil,           name='perfil'),
    path('perfil/password/',   views.cambiar_password, name='cambiar_password'),
]