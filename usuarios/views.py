from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from correspondencia.models import Documento
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


def sin_permisos(request):
    """
    Página que se muestra cuando el usuario no tiene permisos suficientes.
    """
    return render(request, 'errors/sin_permisos.html', status=403)


@login_required
def dashboard(request):
    hoy = timezone.now().date()
    total      = Documento.objects.count()
    en_tramite = Documento.objects.filter(estado='en_tramite').count()
    recibidos  = Documento.objects.filter(estado='recibido').count()
    vencidos   = Documento.objects.filter(
        fecha_limite__lt=hoy
    ).exclude(estado__in=['respondido', 'archivado']).count()
    recientes  = Documento.objects.select_related('responsable', 'radicado_por').order_by('-fecha_radicacion')[:10]
    urgentes   = Documento.objects.filter(
        prioridad='urgente'
    ).exclude(estado__in=['respondido', 'archivado']).order_by('fecha_limite')[:5]

    return render(request, 'base/dashboard.html', {
        'total':      total,
        'en_tramite': en_tramite,
        'recibidos':  recibidos,
        'vencidos':   vencidos,
        'recientes':  recientes,
        'urgentes':   urgentes,
        'hoy':        hoy,
    })


@login_required
@permission_required('usuarios.change_usuario', False)
def usuario_lista(request):
    from .models import Usuario
    from django.contrib import messages
    usuarios = Usuario.objects.all().order_by('last_name')
    return render(request, 'usuarios/lista.html', {'usuarios': usuarios})

@login_required
def perfil(request):
    if request.method == 'POST':
        # Actualizar datos personales
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name',  user.last_name)
        user.email      = request.POST.get('email',      user.email)
        user.cargo      = request.POST.get('cargo',      user.cargo)
        user.telefono   = request.POST.get('telefono',   user.telefono)

        # Firma digital
        if 'firma' in request.FILES:
            user.firma = request.FILES['firma']

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('perfil')

    return render(request, 'usuarios/perfil.html', {'usuario': request.user})


@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '✅ Contraseña cambiada exitosamente.')
            return redirect('perfil')
        else:
            messages.error(request, '❌ Por favor corrige los errores.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'usuarios/cambiar_password.html', {'form': form})