"""
URLs principales del Sistema de Correspondencia CER
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # Redirección raíz → login
    path('', RedirectView.as_view(url='/login/', permanent=False)),

    # Módulos del sistema
    path('', include('usuarios.urls')),
    path('', include('correspondencia.urls')),
    path('', include('plantillas.urls')),
    path('', include('reportes.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalizar el admin de Django
admin.site.site_header = 'CER — Administración del Sistema'
admin.site.site_title = 'CER Sistema'
admin.site.index_title = 'Panel de Control'