"""
Vistas con Rate Limiting para seguridad del sistema CER.
Protege login y operaciones críticas contra ataques de fuerza bruta.
"""
from django.contrib.auth.views import LoginView
from django_ratelimit.decorators import ratelimit
from django.contrib import messages
from django.shortcuts import redirect, render


class LoginViewConRateLimit(LoginView):
    """
    Vista de login personalizada con Rate Limiting.
    Límite: 5 intentos por minuto por IP
    """
    template_name = 'usuarios/login.html'
    
    def post(self, request, *args, **kwargs):
        """
        POST handler con rate limit decorator.
        Si se supera el límite, redirige a página de error amigable.
        """
        # Aplicar rate limit y verificar
        response = self._handle_post_with_ratelimit(request, *args, **kwargs)
        return response
    
    @ratelimit(key='ip', rate='5/m', method='POST', block=False)
    def _handle_post_with_ratelimit(self, request, *args, **kwargs):
        """
        Wrapper para aplicar rate limit al POST.
        """
        # Si fue limitado, redirigir   
        if getattr(request, 'limited', False):
            messages.error(
                request,
                '🔒 Demasiados intentos de login. Por favor, espera 1 minuto antes de intentar nuevamente.'
            )
            return redirect('login_rate_limit_exceeded')
        
        # Si no fue limitado, procesar login normal
        return super().post(request, *args, **kwargs)


def login_rate_limit_exceeded(request):
    """
    Página amigable cuando se supera el límite de rate limiting en login.
    """
    return render(request, 'usuarios/login_rate_limit.html', status=429)


def radicacion_rate_limit_exceeded(request):
    """
    Página amigable cuando se supera el límite de rate limiting en radicación.
    """
    return render(request, 'correspondencia/radicacion_rate_limit.html', status=429)
