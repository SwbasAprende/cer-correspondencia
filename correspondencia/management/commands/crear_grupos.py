"""
Management command para crear los grupos del sistema
Uso: python manage.py crear_grupos
"""
from django.core.management.base import BaseCommand
from correspondencia.grupos import crear_grupos_sistema


class Command(BaseCommand):
    help = 'Crea los grupos del sistema (Administrador, Radicador, Consultor, Solo lectura)'

    def handle(self, *args, **options):
        """
        Ejecuta la creación de grupos
        """
        try:
            crear_grupos_sistema()
            self.stdout.write(
                self.style.SUCCESS('✅ Grupos creados exitosamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear grupos: {str(e)}')
            )
