from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'rol', 'cargo', 'activo_sistema']
    list_filter   = ['rol', 'activo_sistema']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('Información CER', {
            'fields': ('rol', 'cargo', 'telefono', 'firma', 'activo_sistema')
        }),
    )