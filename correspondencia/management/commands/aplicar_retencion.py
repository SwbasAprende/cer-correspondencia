"""
Comando para aplicar retención documental según TRD (Ley 594).
Busca documentos que han superado su tiempo de retención y genera reportes.
Nunca elimina documentos automáticamente — solo marca para revisión.

Uso: python manage.py aplicar_retencion [--aplicar] [--dias=D]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from correspondencia.models import Documento, TRD
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Aplica retención documental según TRD — Ley 594 de 2000'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Marcar documentos para revisión (no elimina)',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=0,
            help='Días adicionales para considerar vencidos (default: 0)',
        )

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('📋 APLICACIÓN DE RETENCIÓN DOCUMENTAL — LEY 594'))
        self.stdout.write('='*80 + '\n')

        hoy = timezone.now().date()
        dias_extra = options['dias']
        aplicar = options['aplicar']

        self.stdout.write(f'Fecha de referencia: {hoy}')
        if dias_extra > 0:
            self.stdout.write(f'Días adicionales considerados: {dias_extra}')
        self.stdout.write(f'Modo aplicar: {"SÍ" if aplicar else "NO (solo reporte)"}')
        self.stdout.write('')

        # Obtener documentos con TRD activo
        documentos_con_trd = []
        documentos_sin_trd = []

        # Buscar todos los documentos
        documentos = Documento.objects.select_related('responsable', 'radicado_por').all()

        for doc in documentos:
            # Buscar TRD correspondiente
            trd = TRD.objects.filter(
                tipo_documental=doc.tipo,
                activo=True
            ).first()

            if trd:
                # Calcular fecha límite de retención en gestión
                fecha_limite_gestion = doc.fecha_radicacion + timedelta(days=trd.retencion_gestion * 365)
                fecha_limite_gestion = fecha_limite_gestion.replace(day=31, month=12)  # Fin de año

                # Considerar días extra si se especifica
                fecha_limite_ajustada = fecha_limite_gestion + timedelta(days=dias_extra)

                if hoy > fecha_limite_ajustada:
                    documentos_con_trd.append({
                        'documento': doc,
                        'trd': trd,
                        'fecha_limite': fecha_limite_gestion,
                        'dias_vencidos': (hoy - fecha_limite_gestion).days,
                        'disposicion': trd.disposicion_final,
                    })
            else:
                # Documento sin TRD definido
                documentos_sin_trd.append(doc)

        # Reporte de documentos con TRD vencido
        if documentos_con_trd:
            self.stdout.write(self.style.WARNING(f'⚠️  DOCUMENTOS CON RETENCIÓN VENCIDA: {len(documentos_con_trd)}'))
            self.stdout.write('-' * 80)
            self.stdout.write(f"{'Radicado':<15} {'Tipo':<8} {'Fecha':<12} {'Vencido':<10} {'Disposición':<12}")
            self.stdout.write('-' * 80)

            for item in documentos_con_trd:
                doc = item['documento']
                self.stdout.write(
                    f"{doc.radicado:<15} "
                    f"{doc.get_tipo_display():<8} "
                    f"{doc.fecha_radicacion.strftime('%d/%m/%Y'):<12} "
                    f"{item['dias_vencidos']:<10} "
                    f"{item['trd'].get_disposicion_final_display():<12}"
                )

                if aplicar:
                    # Marcar documento para revisión (cambiar estado si no está archivado)
                    if doc.estado != 'archivado':
                        doc.estado = 'en_tramite'  # Estado de revisión
                        doc.save()
                        self.stdout.write(f"  → Marcado para revisión")
                    else:
                        self.stdout.write(f"  → Ya archivado, no se modifica")

            self.stdout.write('')
        else:
            self.stdout.write(self.style.SUCCESS('✅ No hay documentos con retención vencida'))

        # Reporte de documentos sin TRD
        if documentos_sin_trd:
            self.stdout.write(self.style.ERROR(f'❌ DOCUMENTOS SIN TRD DEFINIDO: {len(documentos_sin_trd)}'))
            self.stdout.write('-' * 80)
            for doc in documentos_sin_trd[:10]:  # Mostrar máximo 10
                self.stdout.write(f"{doc.radicado} — {doc.get_tipo_display()} — {doc.fecha_radicacion}")
            if len(documentos_sin_trd) > 10:
                self.stdout.write(f"... y {len(documentos_sin_trd) - 10} más")
            self.stdout.write('')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Todos los documentos tienen TRD definido'))

        # Resumen final
        self.stdout.write('='*80)
        total_documentos = len(documentos_con_trd) + len(documentos_sin_trd)
        self.stdout.write(self.style.SUCCESS(
            f'RESUMEN: {total_documentos} documentos analizados'
        ))
        if documentos_con_trd:
            self.stdout.write(self.style.WARNING(
                f'  • {len(documentos_con_trd)} requieren atención según TRD'
            ))
        if documentos_sin_trd:
            self.stdout.write(self.style.ERROR(
                f'  • {len(documentos_sin_trd)} sin TRD definido (revisar)'
            ))

        if aplicar and documentos_con_trd:
            self.stdout.write(self.style.SUCCESS(
                f'  • {len([d for d in documentos_con_trd if d["documento"].estado != "archivado"])} marcados para revisión'
            ))

        self.stdout.write('='*80 + '\n')

        # Logging para auditoría
        logger.info(
            f'Retención documental aplicada: {len(documentos_con_trd)} vencidos, '
            f'{len(documentos_sin_trd)} sin TRD, aplicar={aplicar}'
        )