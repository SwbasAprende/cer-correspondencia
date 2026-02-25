from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from correspondencia.models import Documento
import openpyxl
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
import datetime


# ── Colores institucionales CER ──────────────────────────────────────────────
VERDE_OSCURO  = "1A3A2A"
VERDE_MEDIO   = "2D6A4F"
VERDE_CLARO   = "E8F5E9"
BLANCO        = "FFFFFF"
GRIS_CLARO    = "F5F5F5"
GRIS_BORDE    = "DDDDDD"
ROJO_VENCIDO  = "FFEBEE"
NARANJA_URGENTE = "FFF3E0"


def _borde_delgado():
    lado = Side(style='thin', color=GRIS_BORDE)
    return Border(left=lado, right=lado, top=lado, bottom=lado)


def _celda_titulo(ws, fila, col_inicio, col_fin, texto):
    """Escribe un título de sección con fondo verde oscuro."""
    celda = ws.cell(row=fila, column=col_inicio, value=texto)
    celda.font      = Font(bold=True, color=BLANCO, size=10)
    celda.fill      = PatternFill("solid", fgColor=VERDE_OSCURO)
    celda.alignment = Alignment(horizontal='left', vertical='center')
    if col_fin > col_inicio:
        ws.merge_cells(start_row=fila, start_column=col_inicio,
                       end_row=fila, end_column=col_fin)


def _celda_encabezado(celda, texto):
    """Encabezado de columna — fondo verde medio, texto blanco."""
    celda.value     = texto
    celda.font      = Font(bold=True, color=BLANCO, size=9)
    celda.fill      = PatternFill("solid", fgColor=VERDE_MEDIO)
    celda.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    celda.border    = _borde_delgado()


def _celda_dato(celda, valor, par=False, color=None):
    """Celda de dato con fondo alternado."""
    celda.value     = valor
    celda.font      = Font(size=9)
    celda.alignment = Alignment(vertical='center', wrap_text=True)
    celda.border    = _borde_delgado()
    if color:
        celda.fill  = PatternFill("solid", fgColor=color)
    elif par:
        celda.fill  = PatternFill("solid", fgColor=VERDE_CLARO)
    else:
        celda.fill  = PatternFill("solid", fgColor=BLANCO)


@login_required
def reporte_lista(request):
    """Vista del formulario de reportes."""
    contexto = {
        'total': Documento.objects.count(),
        'hoy':   timezone.now().date(),
    }
    return render(request, 'reportes/lista.html', contexto)


@login_required
def exportar_excel(request):
    """Genera y descarga el reporte Excel institucional del CER."""

    # ── Filtro por fechas ────────────────────────────────────────────────────
    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')

    docs = Documento.objects.all().order_by('-fecha_radicacion')

    try:
        if fecha_desde_str:
            fecha_desde = datetime.date.fromisoformat(fecha_desde_str)
            docs = docs.filter(fecha_radicacion__gte=fecha_desde)
        if fecha_hasta_str:
            fecha_hasta = datetime.date.fromisoformat(fecha_hasta_str)
            docs = docs.filter(fecha_radicacion__lte=fecha_hasta)
    except ValueError:
        pass

    docs = list(docs)

    # ── Crear libro Excel ────────────────────────────────────────────────────
    wb = openpyxl.Workbook()

    # ════════════════════════════════════════════════════════════════════════
    # HOJA 1 — RESUMEN
    # ════════════════════════════════════════════════════════════════════════
    ws1 = wb.active
    ws1.title = "Resumen"
    ws1.sheet_view.showGridLines = False
    ws1.column_dimensions['A'].width = 30
    ws1.column_dimensions['B'].width = 15
    ws1.column_dimensions['C'].width = 15
    ws1.column_dimensions['D'].width = 15
    ws1.column_dimensions['E'].width = 15

    fila = 1

    # Encabezado institucional
    ws1.row_dimensions[fila].height = 30
    enc = ws1.cell(row=fila, column=1,
                   value="CENTRO DE ESTUDIOS REGIONALES — CER")
    enc.font      = Font(bold=True, color=VERDE_OSCURO, size=14)
    enc.alignment = Alignment(horizontal='left', vertical='center')
    ws1.merge_cells(f'A{fila}:E{fila}')

    fila += 1
    sub = ws1.cell(row=fila, column=1,
                   value="Reporte de Correspondencia Institucional — Ley 594 de 2000")
    sub.font      = Font(color="555555", size=10, italic=True)
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws1.merge_cells(f'A{fila}:E{fila}')

    fila += 1
    fecha_gen = ws1.cell(row=fila, column=1,
                         value=f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
    fecha_gen.font      = Font(color="888888", size=9)
    fecha_gen.alignment = Alignment(horizontal='left')
    ws1.merge_cells(f'A{fila}:E{fila}')

    if fecha_desde_str or fecha_hasta_str:
        fila += 1
        rango_txt = f"Período: {fecha_desde_str or 'inicio'} al {fecha_hasta_str or 'hoy'}"
        rango_cel = ws1.cell(row=fila, column=1, value=rango_txt)
        rango_cel.font      = Font(color="888888", size=9, italic=True)
        rango_cel.alignment = Alignment(horizontal='left')
        ws1.merge_cells(f'A{fila}:E{fila}')

    fila += 2

    # ── Estadísticas generales ───────────────────────────────────────────────
    _celda_titulo(ws1, fila, 1, 5, "  ESTADÍSTICAS GENERALES")
    ws1.row_dimensions[fila].height = 20
    fila += 1

    stats = [
        ("Total de documentos",          len(docs)),
        ("Documentos recibidos",          sum(1 for d in docs if d.estado == 'recibido')),
        ("Documentos en trámite",         sum(1 for d in docs if d.estado == 'en_tramite')),
        ("Documentos respondidos",        sum(1 for d in docs if d.estado == 'respondido')),
        ("Documentos archivados",         sum(1 for d in docs if d.estado == 'archivado')),
        ("Documentos vencidos",           sum(1 for d in docs if d.esta_vencido)),
        ("Documentos urgentes",           sum(1 for d in docs if d.prioridad == 'urgente')),
        ("Documentos confidenciales",     sum(1 for d in docs if d.prioridad == 'confidencial')),
    ]

    for i, (etiqueta, valor) in enumerate(stats):
        ws1.row_dimensions[fila].height = 18
        _celda_dato(ws1.cell(row=fila, column=1), etiqueta, par=(i % 2 == 0))
        c_val = ws1.cell(row=fila, column=2, value=valor)
        c_val.font      = Font(bold=True, size=11, color=VERDE_OSCURO)
        c_val.alignment = Alignment(horizontal='center', vertical='center')
        c_val.border    = _borde_delgado()
        if i % 2 == 0:
            c_val.fill = PatternFill("solid", fgColor=VERDE_CLARO)
        fila += 1

    fila += 2

    # ── Documentos por tipo ──────────────────────────────────────────────────
    _celda_titulo(ws1, fila, 1, 5, "  DOCUMENTOS POR TIPO")
    ws1.row_dimensions[fila].height = 20
    fila += 1

    encabezados_tipo = ["Tipo", "Total", "Recibidos", "En Trámite", "Respondidos"]
    for col, txt in enumerate(encabezados_tipo, 1):
        _celda_encabezado(ws1.cell(row=fila, column=col), txt)
    ws1.row_dimensions[fila].height = 20
    fila_inicio_grafico = fila

    tipos_labels = []
    tipos_valores = []

    for i, (codigo, nombre) in enumerate(Documento.Tipo.choices):
        docs_tipo = [d for d in docs if d.tipo == codigo]
        if not docs_tipo:
            continue
        ws1.row_dimensions[fila].height = 18
        _celda_dato(ws1.cell(row=fila, column=1), nombre,            par=(i % 2 == 0))
        _celda_dato(ws1.cell(row=fila, column=2), len(docs_tipo),    par=(i % 2 == 0))
        _celda_dato(ws1.cell(row=fila, column=3),
                    sum(1 for d in docs_tipo if d.estado == 'recibido'),   par=(i % 2 == 0))
        _celda_dato(ws1.cell(row=fila, column=4),
                    sum(1 for d in docs_tipo if d.estado == 'en_tramite'), par=(i % 2 == 0))
        _celda_dato(ws1.cell(row=fila, column=5),
                    sum(1 for d in docs_tipo if d.estado == 'respondido'), par=(i % 2 == 0))
        tipos_labels.append(nombre)
        tipos_valores.append(len(docs_tipo))
        fila += 1

    fila_fin_grafico = fila - 1
    fila += 2

    # ── Gráfico de barras por tipo ───────────────────────────────────────────
    if tipos_valores:
        chart = BarChart()
        chart.type    = "col"
        chart.title   = "Documentos por Tipo"
        chart.y_axis.title = "Cantidad"
        chart.x_axis.title = "Tipo"
        chart.style   = 10
        chart.width   = 18
        chart.height  = 10

        data = Reference(ws1,
                         min_col=2, max_col=2,
                         min_row=fila_inicio_grafico,
                         max_row=fila_fin_grafico)
        cats = Reference(ws1,
                         min_col=1,
                         min_row=fila_inicio_grafico + 1,
                         max_row=fila_fin_grafico)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        ws1.add_chart(chart, f"A{fila}")

    # ════════════════════════════════════════════════════════════════════════
    # HOJA 2 — DETALLE
    # ════════════════════════════════════════════════════════════════════════
    ws2 = wb.create_sheet("Detalle")
    ws2.sheet_view.showGridLines = False

    # Anchos de columna
    anchos = [12, 18, 10, 10, 12, 25, 25, 25, 40, 12, 12, 12, 20, 20]
    for i, ancho in enumerate(anchos, 1):
        ws2.column_dimensions[get_column_letter(i)].width = ancho

    # Encabezado institucional hoja 2
    ws2.row_dimensions[1].height = 28
    enc2 = ws2.cell(row=1, column=1,
                    value="CENTRO DE ESTUDIOS REGIONALES — CER · Detalle de Correspondencia")
    enc2.font      = Font(bold=True, color=VERDE_OSCURO, size=12)
    enc2.alignment = Alignment(horizontal='left', vertical='center')
    ws2.merge_cells('A1:N1')

    ws2.row_dimensions[2].height = 18
    sub2 = ws2.cell(row=2, column=1,
                    value=f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M')}  |  Total: {len(docs)} documentos")
    sub2.font      = Font(color="888888", size=9, italic=True)
    sub2.alignment = Alignment(horizontal='left', vertical='center')
    ws2.merge_cells('A2:N2')

    # Encabezados de columnas
    fila2 = 4
    ws2.row_dimensions[fila2].height = 30
    cols = [
        "Radicado", "Fecha Radicación", "Tipo", "Flujo",
        "Prioridad", "Remitente", "Destinatario", "Entidad",
        "Asunto", "Estado", "Fecha Límite", "Fecha Respuesta",
        "Responsable", "Radicado Por"
    ]
    for col, txt in enumerate(cols, 1):
        _celda_encabezado(ws2.cell(row=fila2, column=col), txt)

    fila2 += 1

    for i, doc in enumerate(docs):
        ws2.row_dimensions[fila2].height = 16
        par = (i % 2 == 0)

        # Color especial para vencidos y urgentes
        if doc.esta_vencido:
            color_fila = ROJO_VENCIDO.replace("#", "")
        elif doc.prioridad == 'urgente':
            color_fila = NARANJA_URGENTE.replace("#", "")
        else:
            color_fila = None

        valores = [
            doc.radicado,
            doc.fecha_radicacion.strftime('%d/%m/%Y') if doc.fecha_radicacion else '',
            doc.get_tipo_display(),
            doc.get_flujo_display(),
            doc.get_prioridad_display(),
            doc.remitente,
            doc.destinatario,
            doc.entidad or '',
            doc.asunto,
            doc.get_estado_display(),
            doc.fecha_limite.strftime('%d/%m/%Y') if doc.fecha_limite else '',
            doc.fecha_respuesta.strftime('%d/%m/%Y') if doc.fecha_respuesta else '',
            str(doc.responsable) if doc.responsable else '',
            str(doc.radicado_por) if doc.radicado_por else '',
        ]

        for col, valor in enumerate(valores, 1):
            _celda_dato(ws2.cell(row=fila2, column=col), valor,
                        par=par, color=color_fila)

        fila2 += 1

    # ── Generar respuesta HTTP ───────────────────────────────────────────────
    nombre_archivo = f"reporte_CER_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    wb.save(response)
    return response