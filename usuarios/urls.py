from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from .ratelimit_views import LoginViewConRateLimit, login_rate_limit_exceeded, radicacion_rate_limit_exceeded

urlpatterns = [
    path('login/',    LoginViewConRateLimit.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/',   LogoutView.as_view(), name='logout'),
    path('login-rate-limit/', login_rate_limit_exceeded, name='login_rate_limit_exceeded'),
    path('radicacion-rate-limit/', radicacion_rate_limit_exceeded, name='radicacion_rate_limit_exceeded'),
    path('sin-permisos/', views.sin_permisos, name='sin_permisos'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('usuarios/', views.usuario_lista, name='usuario_lista'),
    path('perfil/',            views.perfil,           name='perfil'),
    path('perfil/password/',   views.cambiar_password, name='cambiar_password'),
]