# MANUAL DEL ADMINISTRADOR - Sistema CER

## 1. Cómo crear usuarios y asignar grupos
1. Iniciar sesión en /admin/ con usuario administrador.
2. Ir a Usuarios > Usuarios y crear nuevo usuario.
3. Asignar un grupo válido (Administrador, Radicador, Consultor, Solo lectura).
4. Confirmar `activo_sistema` y rol adecuado.

## 2. Cómo usar el panel /admin/
- Gestión de modelos: Documentos, TRD, AccesoDocumento, AuditoriaDocumento.
- Revisar logs de auditoría y accesos para cumplimiento.

## 3. Cómo ejecutar comandos de mantenimiento
- `python manage.py crear_grupos` (crear roles base).
- `python manage.py verificar_produccion` (chequeo de entorno).
- `python manage.py aplicar_retencion` (retención documental).
- `python manage.py verificar_vencimientos` (alertas de documentos vencidos).

## 4. Cómo interpretar logs y alertas
- Revisar `SENTRY_DSN` en entornos productivos.
- Logs de seguridad en consola con etiquetas `correspondencia`, `usuarios`.
- Alertas por `django_ratelimit` para intentos excesivos.

## 5. Procedimiento de backup
- Backup diario de base de datos (PostgreSQL/SQLite).
- Backup semanal de archivos en `media/documentos/`.
- Verificar restauración periódica en entorno de pruebas.
