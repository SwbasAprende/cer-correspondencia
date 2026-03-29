# POLÍTICA DE SEGURIDAD - Sistema CER

## 1. Política de contraseñas
- Longitud mínima: 12 caracteres.
- Deben incluir mayúsculas, minúsculas, dígitos y símbolos.
- Expiración cada 90 días.
- No reutilizar las últimas 5 contraseñas.
- Hash seguro con Argon2.

## 2. Roles y permisos
- `administrador`: acceso total al sistema. Gestión de usuarios, TRD, documentos, reportes.
- `director`: radicar y gestionar documentos, ver confidenciales.
- `consulta`: solo consulta, sin permiso de radicación ni edición.

Permisos clave:
- correspondencia.add_documento
- correspondencia.change_documento
- correspondencia.view_documento
- correspondencia.view_confidenciales
- usuarios.change_usuario

## 3. Procedimiento de acceso y revocación
1. Solicitud formal de acceso por correo institucional.
2. Validación por el responsable de TI.
3. Creación de usuario en Django Admin y asignación de grupo.
4. Revocación: desactivar usuario (`activo_sistema = False`) y remover grupo.
5. Registro de cambios en bitácora interna.

## 4. Política de retención documental (Ley 594)
- Se utiliza la Tabla de Retención Documental (TRD) de la aplicación.
- No se eliminan documentos automáticamente: se marcan para revisión.
- El comando `python manage.py aplicar_retencion` produce reporte de documentos con vencimiento en retención.

## 5. Contacto del responsable de sistema
- Nombre: Coordinador TI CER
- Email: soporte-cer@cer.gov.co
- Móvil: +57 300 000 0000
