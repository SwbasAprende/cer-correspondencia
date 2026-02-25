from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from correspondencia.models import Documento


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
def usuario_lista(request):
    from .models import Usuario
    from django.contrib import messages
    if not request.user.puede_gestionar_usuarios:
        messages.error(request, 'No tienes permiso para ver esta sección.')
        return redirect('dashboard')
    usuarios = Usuario.objects.all().order_by('last_name')
    return render(request, 'usuarios/lista.html', {'usuarios': usuarios})