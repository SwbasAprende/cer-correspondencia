from .notificaciones import notificar_nuevo_documento, notificar_cambio_estado
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Documento, Trazabilidad, AccesoDocumento, AuditoriaDocumento
from .forms import DocumentoForm
from .utils import registrar_acceso
from openpyxl import workbook
from django.http import HttpResponse
from django.utils import timezone
from weasyprint import HTML
from django.template.loader import render_to_string

@login_required
def documento_lista(request):
    docs = Documento.objects.select_related('responsable', 'radicado_por').order_by('-fecha_radicacion')

    # Control de acceso a documentos confidenciales
    if not request.user.has_perm('correspondencia.view_confidenciales'):
        docs = docs.exclude(prioridad=Documento.Prioridad.CONFIDENCIAL)

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
            Q(radicado__icontains=buscar) |
            Q(asunto__icontains=buscar) |
            Q(remitente__icontains=buscar) |
            Q(destinatario__icontains=buscar)
        ).distinct()

    total = docs.count()
    paginator = Paginator(docs, 20)
    page = request.GET.get('page', 1)
    try:
        documentos_page = paginator.page(page)
    except PageNotAnInteger:
        documentos_page = paginator.page(1)
    except EmptyPage:
        documentos_page = paginator.page(paginator.num_pages)

    contexto = {
        'documentos':    documentos_page,
        'page_obj':      documentos_page,
        'paginator':     paginator,
        'pagina_actual': documentos_page.number,
        'num_paginas':   paginator.num_pages,
        'total':         total,
        'estado_filtro': estado,
        'tipo_filtro':   tipo,
        'prioridad':     prioridad,
        'buscar':        buscar,
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
            cache.delete('dashboard_estadisticas')
            notificar_nuevo_documento(doc)
            messages.success(request, f'Documento radicado exitosamente con número {doc.radicado}')
            return redirect('documento_detalle', pk=doc.pk)
    else:
        form = DocumentoForm()

    return render(request, 'correspondencia/nuevo.html', {'form': form})


@login_required
def documento_detalle(request, pk):
    doc = get_object_or_404(
        Documento.objects.select_related('responsable', 'radicado_por').prefetch_related('trazabilidad'),
        pk=pk
    )
    trazabilidad = doc.trazabilidad.all().order_by('-fecha')

    # Registrar acceso para auditoría (Ley 594)
    registrar_acceso(request, doc, AccesoDocumento.Accion.VER)

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
            cache.delete('dashboard_estadisticas')
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
            # Guardar valores anteriores para auditoría
            valores_anteriores = {}
            campos_auditar = [
                'tipo', 'flujo', 'prioridad', 'actor', 'remitente', 'destinatario',
                'entidad', 'asunto', 'descripcion', 'fecha_documento', 'responsable',
                'documento_referencia'
            ]
            
            for campo in campos_auditar:
                valor_actual = getattr(doc, campo)
                if valor_actual is not None:
                    valores_anteriores[campo] = str(valor_actual)
                else:
                    valores_anteriores[campo] = ''

            # Guardar cambios
            form.save()
            
            # Registrar auditoría de cambios (Ley 594)
            ip_address = None
            if hasattr(request, 'META'):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0].strip()
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
            
            for campo in campos_auditar:
                valor_anterior = valores_anteriores.get(campo, '')
                valor_nuevo = str(getattr(doc, campo) or '')
                
                if valor_anterior != valor_nuevo:
                    AuditoriaDocumento.objects.create(
                        documento=doc,
                        usuario=request.user,
                        campo_modificado=campo,
                        valor_anterior=valor_anterior,
                        valor_nuevo=valor_nuevo,
                        ip_address=ip_address,
                    )
            
            cache.delete('dashboard_estadisticas')
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

    # Registrar acceso para auditoría (Ley 594)
    registrar_acceso(request, doc, AccesoDocumento.Accion.IMPRIMIR)

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

@login_required
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

    queryset = Documento.objects.all()

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
            c.radicado,
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