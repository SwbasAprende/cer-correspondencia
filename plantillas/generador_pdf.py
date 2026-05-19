"""
Generador de PDFs institucionales con membrete CER
Usa ReportLab para crear documentos con formato profesional
"""
import os
import io
from datetime import date
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


# ── Colores institucionales CER ───────────────────────────────────────────────
VERDE_OSCURO = HexColor('#1b4332')
VERDE_MEDIO  = HexColor('#2d6a4f')
DORADO       = HexColor('#d4a017')
GRIS_CLARO   = HexColor('#f8f9fa')
GRIS_MEDIO   = HexColor('#6c757d')


def get_estilos():
    """Estilos tipográficos institucionales del CER"""
    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        name='CER_Titulo',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=VERDE_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    estilos.add(ParagraphStyle(
        name='CER_Subtitulo',
        fontName='Helvetica',
        fontSize=9,
        textColor=GRIS_MEDIO,
        alignment=TA_CENTER,
        spaceAfter=2,
    ))
    estilos.add(ParagraphStyle(
        name='CER_TipoDoc',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=white,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))
    estilos.add(ParagraphStyle(
        name='CER_Radicado',
        fontName='Courier-Bold',
        fontSize=9,
        textColor=VERDE_OSCURO,
        alignment=TA_RIGHT,
        spaceAfter=2,
    ))
    estilos.add(ParagraphStyle(
        name='CER_Etiqueta',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=VERDE_OSCURO,
        spaceAfter=2,
    ))
    estilos.add(ParagraphStyle(
        name='CER_Valor',
        fontName='Helvetica',
        fontSize=9,
        textColor=black,
        spaceAfter=2,
    ))
    estilos.add(ParagraphStyle(
        name='CER_Cuerpo',
        fontName='Helvetica',
        fontSize=10,
        textColor=black,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=16,
    ))
    estilos.add(ParagraphStyle(
        name='CER_Firma',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=VERDE_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=2,
    ))
    estilos.add(ParagraphStyle(
        name='CER_FirmaSub',
        fontName='Helvetica',
        fontSize=9,
        textColor=GRIS_MEDIO,
        alignment=TA_CENTER,
        spaceAfter=2,
    ))
    estilos.add(ParagraphStyle(
        name='CER_Pie',
        fontName='Helvetica',
        fontSize=7,
        textColor=GRIS_MEDIO,
        alignment=TA_CENTER,
        spaceAfter=0,
    ))
    return estilos


def construir_membrete(estilos, config):
    """Construye el membrete institucional del CER con logo"""
    elementos = []

    # Intentar cargar el logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_actualizado_cer.jpeg')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_actualizado_cer.jpeg')

    if os.path.exists(logo_path):
        # Membrete con logo
        logo = Image(logo_path, width=3.5*cm, height=2*cm)
        logo.hAlign = 'LEFT'

        datos_entidad = [
            Paragraph(f"<b>{config['nombre']}</b>", estilos['CER_Titulo']),
            Paragraph(config.get('nit', ''), estilos['CER_Subtitulo']),
            Paragraph(config.get('direccion', ''), estilos['CER_Subtitulo']),
            Paragraph(config.get('ciudad', ''), estilos['CER_Subtitulo']),
        ]
        if config.get('email'):
            datos_entidad.append(Paragraph(config['email'], estilos['CER_Subtitulo']))
        if config.get('telefono'):
            datos_entidad.append(Paragraph(config['telefono'], estilos['CER_Subtitulo']))

        tabla_membrete = Table(
            [[logo, datos_entidad]],
            colWidths=[4*cm, 13*cm]
        )
        tabla_membrete.setStyle(TableStyle([
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',      (0, 0), (0, 0),   'LEFT'),
            ('ALIGN',      (1, 0), (1, 0),   'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(tabla_membrete)
    else:
        # Membrete solo texto si no hay logo
        elementos.append(Paragraph(config['nombre'], estilos['CER_Titulo']))
        if config.get('nit'):
            elementos.append(Paragraph(f"NIT: {config['nit']}", estilos['CER_Subtitulo']))
        if config.get('direccion'):
            elementos.append(Paragraph(config['direccion'], estilos['CER_Subtitulo']))

    # Línea separadora dorada
    elementos.append(HRFlowable(
        width='100%', thickness=2,
        color=DORADO, spaceAfter=4
    ))
    elementos.append(HRFlowable(
        width='100%', thickness=0.5,
        color=VERDE_MEDIO, spaceAfter=8
    ))
    return elementos


def construir_encabezado_documento(estilos, documento, tipo_label):
    """Banda verde con el tipo de documento y número de radicado"""
    elementos = []

    tabla_tipo = Table(
        [[Paragraph(tipo_label.upper(), estilos['CER_TipoDoc'])]],
        colWidths=[17*cm]
    )
    tabla_tipo.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), VERDE_OSCURO),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elementos.append(tabla_tipo)
    elementos.append(Spacer(1, 8))

    # Radicado y fecha
    fecha_str = documento.fecha_radicacion.strftime('%d/%m/%Y')
    hora_str  = documento.hora_radicacion.strftime('%H:%M:%S')
    elementos.append(Paragraph(
        f"Radicado: <b>{documento.radicado}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Fecha: <b>{fecha_str}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Hora: <b>{hora_str}</b>",
        estilos['CER_Radicado']
    ))
    elementos.append(Spacer(1, 8))
    return elementos


def construir_destinatario(estilos, documento):
    """Bloque Para/De/Asunto"""
    elementos = []

    ciudad = settings.CER_CONFIG.get('ciudad', 'Colombia')
    fecha_larga = documento.fecha_radicacion.strftime('%d de %B de %Y').replace(
        'January','enero').replace('February','febrero').replace('March','marzo'
        ).replace('April','abril').replace('May','mayo').replace('June','junio'
        ).replace('July','julio').replace('August','agosto').replace('September','septiembre'
        ).replace('October','octubre').replace('November','noviembre').replace('December','diciembre')

    elementos.append(Paragraph(f"{ciudad}, {fecha_larga}", estilos['CER_Valor']))
    elementos.append(Spacer(1, 12))

    datos = [
        ['Para:', documento.destinatario],
        ['De:', documento.remitente],
    ]
    if documento.entidad:
        datos.append(['Entidad:', documento.entidad])
    datos.append(['Asunto:', documento.asunto])
    datos.append(['Prioridad:', documento.get_prioridad_display()])

    tabla_dest = Table(datos, colWidths=[3*cm, 14*cm])
    tabla_dest.setStyle(TableStyle([
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',  (0, 0), (0, -1), VERDE_OSCURO),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW',  (0, -1), (-1, -1), 0.5, GRIS_MEDIO),
    ]))
    elementos.append(tabla_dest)
    elementos.append(Spacer(1, 16))
    return elementos


def construir_firma(estilos, firmante_nombre, firmante_cargo):
    """Bloque de firma al final del documento"""
    elementos = []
    elementos.append(Spacer(1, 40))
    elementos.append(HRFlowable(width=6*cm, thickness=0.5, color=VERDE_OSCURO, spaceAfter=4))
    elementos.append(Paragraph(firmante_nombre, estilos['CER_Firma']))
    elementos.append(Paragraph(firmante_cargo, estilos['CER_FirmaSub']))
    elementos.append(Paragraph(settings.CER_CONFIG.get('nombre', 'CER'), estilos['CER_FirmaSub']))
    return elementos


def construir_pie_pagina(estilos, radicado):
    """Pie de página con información legal"""
    elementos = []
    elementos.append(Spacer(1, 20))
    elementos.append(HRFlowable(width='100%', thickness=0.5, color=DORADO, spaceAfter=4))
    config = settings.CER_CONFIG
    elementos.append(Paragraph(
        f"{config.get('nombre','')} &nbsp;|&nbsp; "
        f"NIT: {config.get('nit','')} &nbsp;|&nbsp; "
        f"{config.get('ciudad','')} &nbsp;|&nbsp; "
        f"Radicado: {radicado} &nbsp;|&nbsp; "
        f"Ley 594 de 2000",
        estilos['CER_Pie']
    ))
    return elementos


# ════════════════════════════════════════════════════════════════════════════
# GENERADORES POR TIPO DE DOCUMENTO
# ════════════════════════════════════════════════════════════════════════════

def generar_pdf(documento, contenido, firmante_nombre, firmante_cargo):
    """
    Función principal — genera el PDF completo según el tipo de documento.
    Retorna un objeto BytesIO con el PDF listo para guardar o descargar.
    """
    buffer = io.BytesIO()
    config = settings.CER_CONFIG
    estilos = get_estilos()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=2.5*cm,
        rightMargin=2.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    elementos = []

    # 1. Membrete
    elementos += construir_membrete(estilos, config)

    # 2. Encabezado con tipo y radicado
    tipo_label = dict(documento.Tipo.choices).get(documento.tipo, documento.tipo)
    elementos += construir_encabezado_documento(estilos, documento, tipo_label)

    # 3. Bloque destinatario/remitente/asunto
    elementos += construir_destinatario(estilos, documento)

    # 4. Cuerpo del documento — párrafo por párrafo
    for parrafo in contenido.strip().split('\n\n'):
        if parrafo.strip():
            elementos.append(Paragraph(parrafo.strip(), estilos['CER_Cuerpo']))

    # 5. Firma
    elementos += construir_firma(estilos, firmante_nombre, firmante_cargo)

    # 6. Pie de página
    elementos += construir_pie_pagina(estilos, documento.radicado)

    doc.build(elementos)
    buffer.seek(0)
    return buffer