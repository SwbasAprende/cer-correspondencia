"""
Decoradores personalizados para control de permisos en el CER
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def permiso_requerido(permiso, mensaje=None):
    """
    Decorador personalizado que valida permisos y redirige adecuadamente.
    
    Uso:
        @permiso_requerido('correspondencia.add_documento')
        def mi_vista(request):
            ...
    
    Args:
        permiso: string en formato 'app.codename'
        mensaje: mensaje personalizado (opcional)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not request.user.has_perm(permiso):
                msg_default = f'No tienes permiso para acceder a esta página.'
                messages.error(request, mensaje or msg_default)
                return redirect('sin_permisos')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
