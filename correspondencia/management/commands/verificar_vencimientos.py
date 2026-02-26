"""
Comando Django para verificar documentos próximos a vencer.
Ejecutar diariamente con un cron job o tarea programada.
Uso: python manage.py verificar_vencimientos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from correspondencia.models import Documento
from correspondencia.notificaciones import notificar_documento_vencido
import datetime


class Command(BaseCommand):
    help = 'Envía alertas de documentos próximos a vencer'

    def handle(self, *args, **kwargs):
        manana = timezone.now().date() + datetime.timedelta(days=1)

        documentos = Documento.objects.filter(
            fecha_limite=manana
        ).exclude(
            estado__in=['respondido', 'archivado']
        )

        self.stdout.write(f'Verificando vencimientos para {manana}...')

        if not documentos.exists():
            self.stdout.write(self.style.SUCCESS('No hay documentos próximos a vencer.'))
            return

        for doc in documentos:
            notificar_documento_vencido(doc)
            self.stdout.write(
                self.style.WARNING(f'  Alerta enviada: {doc.radicado} — {doc.asunto[:40]}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Total alertas enviadas: {documentos.count()}')
        )