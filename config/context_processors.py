from django.conf import settings
import datetime

def cer_contexto(request):
    return {
        'CER_VERSION': settings.CER_CONFIG.get('version_sistema', '1.0'),
        'CER_NOMBRE':  settings.CER_CONFIG.get('nombre', 'CER'),
        'anio_actual': datetime.date.today().year,
    }