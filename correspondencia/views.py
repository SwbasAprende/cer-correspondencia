from .notificaciones import notificar_nuevo_documento, notificar_cambio_estado
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from .models import Documento, Trazabilidad
from .forms import DocumentoForm
from openpyxl import workbook
from django.http import HttpResponse
from django.utils import timezone
from weasyprint import HTML
from django.template.loader import render_to_string

@login_required
def documento_lista(request):
    docs = Documento.objects.all().order_by('-fecha_radicacion')

    # Filtros
    estado    = request.GET.get('estado', '')
    tipo      = request.GET.get('tipo', '')
    prioridad = request.GET.get('prioridad', '')
    buscar    = request.GET.get('buscar', '')

    if estado:
        docs = docs.filter(estado=estado)
    if tipo:
        docs = docs.filter(tipo=tipo)
    if prioridad:
        docs = docs.filter(prioridad=prioridad)
    if buscar:
        docs = docs.filter(
            radicado__icontains=buscar
        ) | docs.filter(
            asunto__icontains=buscar
        ) | docs.filter(
            remitente__icontains=buscar
        ) | docs.filter(
            destinatario__icontains=buscar
        )

    contexto = {
        'documentos':    docs,
        'estado_filtro': estado,
        'tipo_filtro':   tipo,
        'buscar':        buscar,
        'total':         docs.count(),
        'tipos':         Documento.Tipo.choices,
        'estados':       Documento.Estado.choices,
        'prioridades':   Documento.Prioridad.choices,
    }
    return render(request, 'correspondencia/lista.html', contexto)


@login_required
@permission_required('correspondencia.add_documento', raise_exception=False)
@ratelimit(key='user', rate='10/m', method='POST', block=False)
def documento_nuevo(request):
    # Verificar si fue bloqueado por rate limit
    if request.method == 'POST' and getattr(request, 'limited', False):
        messages.error(
            request,
            '⏱️ Has superado el límite de radicaciones (10 por minuto). Por favor, espera antes de intentar nuevamente.'
        )
        return redirect('radicacion_rate_limit_exceeded')
    
    # Permiso verificado por decorador, si llegamos aquí es porque tiene permiso
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.radicado_por    = request.user
            dt = timezone.localtime(timezone.now())
            doc.fecha_radicacion = dt.date()
            doc.hora_radicacion  = dt.time()
            doc.save()
            # Registrar en trazabilidad
            Trazabilidad.objects.create(
                documento    = doc,
                estado_nuevo = doc.estado,
                usuario      = request.user,
                nota         = 'Documento radicado en el sistema.'
            )
            notificar_nuevo_documento(doc)
            messages.success(request, f'Documento radicado exitosamente con número {doc.radicado}')
            return redirect('documento_detalle', pk=doc.pk)
    else:
        form = DocumentoForm()

    return render(request, 'correspondencia/nuevo.html', {'form': form})


@login_required
def documento_detalle(request, pk):
    doc          = get_object_or_404(Documento, pk=pk)
    trazabilidad = doc.trazabilidad.all().order_by('-fecha')

    # Verificar acceso a confidenciales
    if doc.prioridad == 'confidencial' and not request.user.has_perm('correspondencia.view_confidenciales'):
        messages.error(request, 'No tienes permiso para ver documentos confidenciales.')
        return redirect('documento_lista')

    # Cambio de estado (requiere permiso de cambiar documento)
    if request.method == 'POST' and request.user.has_perm('correspondencia.change_documento'):
        nuevo_estado = request.POST.get('nuevo_estado')
        nota         = request.POST.get('nota', '')
        if nuevo_estado and nuevo_estado != doc.estado:
            Trazabilidad.objects.create(
                documento       = doc,
                estado_anterior = doc.estado,
                estado_nuevo    = nuevo_estado,
                usuario         = request.user,
                nota            = nota
            )
            doc.estado = nuevo_estado
            if nuevo_estado == 'respondido':
                doc.fecha_respuesta = timezone.now().date()
            doc.save()
            notificar_cambio_estado(doc, doc.estado, nuevo_estado, request.user, nota)
            messages.success(request, f'Estado actualizado a: {doc.get_estado_display()}')
            return redirect('documento_detalle', pk=doc.pk)

    fecha_rad, hora_rad = doc.fecha_hora_radicacion

    contexto = {
        'documento':    doc,
        'trazabilidad': trazabilidad,
        'estados':      Documento.Estado.choices,
        'fecha_rad':    fecha_rad,
        'hora_rad':     hora_rad,
    }
    return render(request, 'correspondencia/detalle.html', contexto)


@login_required
@permission_required('correspondencia.change_documento', raise_exception=False)
def documento_editar(request, pk):
    doc = get_object_or_404(Documento, pk=pk)

    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento actualizado correctamente.')
            return redirect('documento_detalle', pk=doc.pk)
    else:
        form = DocumentoForm(instance=doc)

    return render(request, 'correspondencia/editar.html', {'form': form, 'documento': doc})

@login_required
def documento_pdf(request, pk):
    """Genera el PDF completo del documento con membrete institucional."""
    doc = get_object_or_404(Documento, pk=pk)

    # Verificar acceso a documentos confidenciales
    if doc.prioridad == 'confidencial' and not request.user.has_perm('correspondencia.view_confidenciales'):
        messages.error(request, 'No tienes permiso para ver documentos confidenciales.')
        return redirect('documento_lista')

    fecha_rad, hora_rad = doc.fecha_hora_radicacion
    trazabilidad = doc.trazabilidad.all().order_by('-fecha')

    contexto = {
        'documento':        doc,
        'trazabilidad':     trazabilidad,
        'fecha_rad':        fecha_rad,
        'hora_rad':         hora_rad,
        'fecha_generacion': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
    }

    html_string = render_to_string('correspondencia/pdf_detalle.html', contexto, request=request)
    pdf_file    = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="CER-{doc.radicado}.pdf"'
    return response


@login_required
def documento_pdf_sticker(request, pk):
    """Genera el PDF del sticker de radicado (tamaño tarjeta)."""
    doc = get_object_or_404(Documento, pk=pk)
    fecha_rad, hora_rad = doc.fecha_hora_radicacion

    contexto = {
        'documento': doc,
        'fecha_rad': fecha_rad,
        'hora_rad':  hora_rad,
    }

    html_string = render_to_string('correspondencia/pdf_sticker.html', contexto, request=request)
    pdf_file    = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="sticker-{doc.radicado}.pdf"'
    return response

def reporte_correspondencia_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Correspondencia"

    # Encabezados institucionales
    ws.append([
        "Número de Radicado",
        "Fecha de Radicación",
        "Hora de Radicación",
        "Tipo",
        "Estado",
        "Prioridad",
        "Remitente",
        "Destinatario",
        "Entidad",
        "Asunto",
        "Radicado por"
    ])

    queryset = Correspondencia.objects.all()

    # 🔹 Reutilizar los filtros existentes
    tipo = request.GET.get("tipo")
    estado = request.GET.get("estado")
    prioridad = request.GET.get("prioridad")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if tipo:
        queryset = queryset.filter(tipo=tipo)

    if estado:
        queryset = queryset.filter(estado=estado)

    if prioridad:
        queryset = queryset.filter(prioridad=prioridad)

    if fecha_inicio and fecha_fin:
        queryset = queryset.filter(
            fecha_radicacion__range=[fecha_inicio, fecha_fin]
        )

    queryset = queryset.order_by("-fecha_radicacion", "-hora_radicacion")

    for c in queryset:
        ws.append([
            c.numero_radicado,
            c.fecha_radicacion.strftime("%d/%m/%Y"),
            c.hora_radicacion.strftime("%H:%M:%S"),
            c.get_tipo_display(),
            c.get_estado_display(),
            c.get_prioridad_display(),
            c.remitente,
            c.destinatario,
            c.entidad,
            c.asunto,
            str(c.radicado_por)
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    fecha_archivo = timezone.localtime(timezone.now()).strftime("%Y%m%d_%H%M")
    response["Content-Disposition"] = (
        f'attachment; filename="reporte_correspondencia_{fecha_archivo}.xlsx"'
    )

    wb.save(response)
    return response