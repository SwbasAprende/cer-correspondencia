import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.conf import settings
from correspondencia.models import Documento
from .models import PlantillaDocumento, DocumentoGenerado
from .generador_pdf import generar_pdf


@login_required
def plantilla_lista(request):
    plantillas = PlantillaDocumento.objects.filter(activa=True)
    tipos = PlantillaDocumento.Tipo.choices
    return render(request, 'plantillas/lista.html', {
        'plantillas': plantillas,
        'tipos': tipos,
    })

@login_required
@permission_required('plantillas.change_plantilladocumento', raise_exception=False)
def plantilla_editar(request, tipo):
    """Editar el contenido base de una plantilla"""
    plantilla, creada = PlantillaDocumento.objects.get_or_create(
        tipo=tipo,
        defaults={
            'nombre': dict(PlantillaDocumento.Tipo.choices).get(tipo, tipo),
            'cuerpo': CONTENIDOS_DEFAULT.get(tipo, 'Escriba el contenido de la plantilla aquí.'),
        }
    )

    if request.method == 'POST':
        plantilla.nombre     = request.POST.get('nombre', plantilla.nombre)
        plantilla.encabezado = request.POST.get('encabezado', '')
        plantilla.cuerpo     = request.POST.get('cuerpo', '')
        plantilla.pie        = request.POST.get('pie', '')
        plantilla.actualizado_por = request.user
        plantilla.save()
        messages.success(request, f'Plantilla de {plantilla.get_tipo_display()} actualizada.')
        return redirect('plantilla_lista')

    return render(request, 'plantillas/editar.html', {'plantilla': plantilla})


@login_required
@permission_required('plantillas.add_documentogenerado', raise_exception=False)
def generar_documento_pdf(request, documento_pk):
    """
    Vista principal: muestra el editor con datos precargados
    y genera el PDF al hacer submit.
    """
    documento = get_object_or_404(Documento, pk=documento_pk)

    # Cargar plantilla base del tipo de documento
    try:
        plantilla = PlantillaDocumento.objects.get(tipo=documento.tipo, activa=True)
        contenido_base = plantilla.cuerpo
    except PlantillaDocumento.DoesNotExist:
        contenido_base = CONTENIDOS_DEFAULT.get(documento.tipo, '')

    if request.method == 'POST':
        contenido       = request.POST.get('contenido', contenido_base)
        firmante_nombre = request.POST.get('firmante_nombre', request.user.get_full_name() or request.user.username)
        firmante_cargo  = request.POST.get('firmante_cargo', request.user.cargo or 'Director')

        # Generar el PDF
        buffer = generar_pdf(documento, contenido, firmante_nombre, firmante_cargo)

        # Guardar registro
        nombre_archivo = f"{documento.radicado}.pdf"
        from django.core.files.base import ContentFile
        doc_generado = DocumentoGenerado(
            documento    = documento,
            plantilla    = PlantillaDocumento.objects.filter(tipo=documento.tipo).first(),
            contenido    = contenido,
            generado_por = request.user,
        )
        doc_generado.archivo_pdf.save(nombre_archivo, ContentFile(buffer.read()))
        buffer.seek(0)
        doc_generado.save()

        messages.success(request, f'PDF generado: {nombre_archivo}')

        # Descargar directamente
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response

    contexto = {
        'documento':      documento,
        'contenido_base': contenido_base,
        'firmante_nombre': request.user.get_full_name() or request.user.username,
        'firmante_cargo':  getattr(request.user, 'cargo', '') or 'Director',
    }
    return render(request, 'plantillas/generar.html', contexto)


@login_required
def descargar_pdf(request, pk):
    """Descargar un PDF ya generado"""
    doc_gen = get_object_or_404(DocumentoGenerado, pk=pk)
    if doc_gen.archivo_pdf:
        return FileResponse(doc_gen.archivo_pdf.open(), content_type='application/pdf')
    messages.error(request, 'Archivo no encontrado.')
    return redirect('documento_detalle', pk=doc_gen.documento.pk)


# ── Contenidos por defecto para cada tipo ─────────────────────────────────────
CONTENIDOS_DEFAULT = {
    'OF': """Reciba un cordial saludo del Centro de Estudios Regionales — CER.

Por medio del presente oficio, nos permitimos comunicarle lo siguiente:

[Escriba aquí el contenido principal del oficio]

Agradecemos su atención y quedamos atentos a cualquier consulta o requerimiento adicional.""",

    'MM': """De conformidad con las funciones asignadas, por medio del presente memorando se informa lo siguiente:

ASUNTO: [Detalle del asunto]

[Escriba aquí el contenido del memorando. Los memorandos son documentos de comunicación interna del CER.]

Se solicita dar trámite al presente memorando dentro de los tiempos establecidos.""",

    'CR': """El Centro de Estudios Regionales — CER, se permite comunicar a todos los interesados:

[Escriba aquí el contenido de la circular. Las circulares son comunicaciones de carácter general dirigidas a múltiples destinatarios.]

La presente circular entra en vigor a partir de la fecha de su expedición.""",

    'RS': """EL CENTRO DE ESTUDIOS REGIONALES — CER

En uso de sus facultades legales y estatutarias, y

CONSIDERANDO:

Que [escriba aquí los considerandos de la resolución],

RESUELVE:

ARTÍCULO PRIMERO: [Escriba el primer artículo resolutivo]

ARTÍCULO SEGUNDO: [Escriba el segundo artículo resolutivo]

ARTÍCULO TERCERO: La presente resolución rige a partir de la fecha de su expedición.""",

    'AC': """ACTA DE REUNIÓN — CENTRO DE ESTUDIOS REGIONALES

Siendo las [hora] del día [fecha], se reunieron en [lugar] las siguientes personas:

ASISTENTES:
- [Nombre y cargo]
- [Nombre y cargo]

ORDEN DEL DÍA:
1. Verificación de quórum
2. [Punto del orden del día]
3. Varios y proposiciones

DESARROLLO DE LA REUNIÓN:

1. VERIFICACIÓN DE QUÓRUM
Se verificó la asistencia y se declaró quórum suficiente para sesionar.

2. [DESARROLLO DE CADA PUNTO]

COMPROMISOS Y CONCLUSIONES:
- [Compromiso] — Responsable: [nombre] — Fecha: [fecha]

Siendo las [hora] se da por terminada la reunión.

Los asistentes firman en constancia de lo acordado.""",
}