# Documentación Técnica
# Sistema de Correspondencia Institucional — CER
# Versión 1.0.0

---

## 1. RESUMEN EJECUTIVO

El Sistema de Correspondencia Institucional del Centro de Estudios Regionales (CER) es una aplicación web desarrollada en Django que centraliza y automatiza la gestión documental de la organización. Permite radicar, clasificar, hacer seguimiento, archivar y generar documentos institucionales en formato PDF, cumpliendo con la Ley 594 de 2000 del Archivo General de la Nación de Colombia.

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Stack Tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Lenguaje | Python | 3.12.3 |
| Framework web | Django | 4.2.9 |
| Base de datos | SQLite | 3 |
| Generación PDF | ReportLab | 4.4.10 |
| Exportación Excel | OpenPyXL | última |
| Servidor producción | Gunicorn | última |
| Archivos estáticos | WhiteNoise | última |
| Variables entorno | python-decouple | última |
| Despliegue | Render | — |

### 2.2 Patrón de Diseño

El sistema sigue el patrón MVT (Model-View-Template) de Django:

- **Model**: Define la estructura de datos (Documento, Usuario, Trazabilidad, etc.)
- **View**: Contiene la lógica de negocio y control de acceso por roles
- **Template**: Presenta la interfaz de usuario con HTML + CSS institucional

### 2.3 Aplicaciones Django

```
config/          → Configuración global del proyecto
correspondencia/ → Núcleo: documentos y trazabilidad
usuarios/        → Autenticación y perfiles con roles
plantillas/      → Plantillas institucionales y generador PDF
reportes/        → Estadísticas y exportación Excel
```

---

## 3. MODELO DE DATOS

### 3.1 Modelo Usuario (usuarios.Usuario)

Extiende AbstractUser de Django con campos institucionales.

| Campo | Tipo | Descripción |
|---|---|---|
| username | CharField | Nombre de usuario (heredado) |
| first_name | CharField | Nombre (heredado) |
| last_name | CharField | Apellido (heredado) |
| email | EmailField | Correo electrónico |
| rol | CharField | administrador / director / consulta |
| cargo | CharField | Cargo institucional en el CER |
| telefono | CharField | Teléfono de contacto |
| firma | ImageField | Imagen de firma digital |
| activo_sistema | BooleanField | Estado en el sistema |
| fecha_creacion | DateTimeField | Fecha de registro |

**Propiedades calculadas:**
- `es_administrador` → bool
- `es_director` → bool
- `puede_radicar` → bool (administrador o director)
- `puede_gestionar_usuarios` → bool (solo administrador)
- `puede_ver_confidenciales` → bool (administrador o director)

### 3.2 Modelo Documento (correspondencia.Documento)

Representa cada documento radicado en el sistema.

| Campo | Tipo | Descripción |
|---|---|---|
| radicado | CharField | Generado automático: CER-OF-2026-001 |
| consecutivo_anio | PositiveIntegerField | Número secuencial por año y tipo |
| tipo | CharField | OF / MM / CR / RS / AC |
| flujo | CharField | entrada / salida |
| prioridad | CharField | normal / urgente / confidencial |
| estado | CharField | recibido / en_tramite / respondido / archivado |
| actor | CharField | Categoría del ecosistema CER |
| remitente | CharField | Nombre del remitente |
| destinatario | CharField | Nombre del destinatario |
| entidad | CharField | Organización o entidad |
| asunto | CharField | Asunto del documento |
| descripcion | TextField | Observaciones adicionales |
| archivo | FileField | Archivo digital (PDF/JPG/PNG) |
| fecha_radicacion | DateField | Fecha de radicación |
| hora_radicacion | TimeField | Hora exacta de radicación |
| fecha_documento | DateField | Fecha del documento original |
| fecha_limite | DateField | Calculada automáticamente según prioridad |
| fecha_respuesta | DateField | Fecha en que se respondió |
| responsable | FK → Usuario | Persona asignada para tramitar |
| radicado_por | FK → Usuario | Quien radicó el documento |
| documento_referencia | FK → self | Documento al que responde |

**Lógica automática en save():**
- Genera el número de radicado: `CER-{tipo}-{año}-{consecutivo:03d}`
- Calcula la fecha límite según prioridad:
  - Normal: +15 días hábiles
  - Urgente: +5 días hábiles
  - Confidencial: +3 días hábiles

**Propiedades calculadas:**
- `esta_vencido` → bool
- `dias_restantes` → int
- `fecha_hora_radicacion` → tuple (fecha_str, hora_str)

### 3.3 Modelo Trazabilidad (correspondencia.Trazabilidad)

Registro inmutable de cambios de estado. Requerido por Ley 594/2000.

| Campo | Tipo | Descripción |
|---|---|---|
| documento | FK → Documento | Documento afectado |
| estado_anterior | CharField | Estado antes del cambio |
| estado_nuevo | CharField | Nuevo estado |
| usuario | FK → Usuario | Quien realizó el cambio |
| fecha | DateTimeField | Timestamp automático |
| nota | TextField | Observación del cambio |

### 3.4 Modelo PlantillaDocumento (plantillas.PlantillaDocumento)

Almacena el contenido base editable de cada tipo de documento.

| Campo | Tipo | Descripción |
|---|---|---|
| tipo | CharField | Tipo de documento (único por tipo) |
| nombre | CharField | Nombre descriptivo |
| encabezado | TextField | Considerandos / texto introductorio |
| cuerpo | TextField | Contenido base editable |
| pie | TextField | Texto de cierre |
| activa | BooleanField | Si está disponible para usar |
| actualizado | DateTimeField | Última actualización |
| actualizado_por | FK → Usuario | Quien actualizó |

### 3.5 Modelo DocumentoGenerado (plantillas.DocumentoGenerado)

Registro de cada PDF generado desde el sistema.

| Campo | Tipo | Descripción |
|---|---|---|
| documento | FK → Documento | Documento radicado origen |
| plantilla | FK → PlantillaDocumento | Plantilla utilizada |
| contenido | TextField | Contenido final del PDF |
| archivo_pdf | FileField | Ruta del PDF generado |
| generado_por | FK → Usuario | Quien generó el PDF |
| fecha | DateTimeField | Fecha y hora de generación |

---

## 4. FLUJOS DEL SISTEMA

### 4.1 Flujo de Radicación

```
1. Usuario accede a "Radicar documento"
2. Completa el formulario (tipo, flujo, remitente, destinatario, asunto, prioridad, actor)
3. Al guardar:
   a. Se genera el número de radicado automáticamente
   b. Se registra la fecha y hora exacta
   c. Se calcula la fecha límite según prioridad
   d. Se crea el primer registro en Trazabilidad (estado: recibido)
   e. Se envía notificación por email al responsable y administradores
4. Sistema redirige al detalle del documento
```

### 4.2 Flujo de Cambio de Estado

```
1. Administrador o Director abre el detalle del documento
2. Selecciona el nuevo estado y escribe una observación
3. Al guardar:
   a. Se registra en Trazabilidad (estado_anterior, estado_nuevo, usuario, nota)
   b. Si estado = "respondido", se registra la fecha_respuesta
   c. Se envía notificación por email al responsable y quien radicó
```

### 4.3 Flujo de Generación de PDF

```
1. Desde el detalle del documento, clic en "Generar PDF"
2. Se abre el editor con el contenido de la plantilla precargado
3. Usuario edita el contenido, nombre del firmante y cargo
4. Al generar:
   a. ReportLab construye el PDF con membrete, logo, radicado, fecha/hora
   b. Se guarda el PDF en media/plantillas/generados/
   c. Se registra en DocumentoGenerado
   d. El PDF se descarga automáticamente
```

### 4.4 Flujo de Alertas de Vencimiento

```
[Cron Job diario]
1. python manage.py verificar_vencimientos
2. Busca documentos con fecha_limite = mañana
3. Excluye estados: respondido, archivado
4. Por cada documento encontrado:
   a. Envía email al responsable
   b. Envía email a todos los administradores
```

---

## 5. CONTROL DE ACCESO

### 5.1 Roles y Permisos

Cada vista está protegida con `@login_required`. Los permisos adicionales se verifican mediante las propiedades del modelo Usuario:

```python
# En cualquier vista:
if not request.user.puede_radicar:
    messages.error(request, 'Sin permiso')
    return redirect('dashboard')
```

### 5.2 Protección de Documentos Confidenciales

Los documentos con `prioridad = 'confidencial'` solo son visibles para administradores y directores. En `documento_lista`:

```python
if not request.user.puede_ver_confidenciales:
    docs = docs.exclude(prioridad='confidencial')
```

---

## 6. GENERADOR DE PDF — ESTRUCTURA

El archivo `plantillas/generador_pdf.py` construye el PDF en 6 bloques:

```
1. Membrete
   ├── Logo institucional (static/img/logo-cer.png)
   ├── Nombre del CER
   ├── NIT, dirección, ciudad, email, teléfono
   └── Líneas separadoras (dorada + verde)

2. Encabezado del documento
   ├── Banda verde con tipo de documento
   └── Número de radicado + fecha + hora

3. Bloque de destinatario
   ├── Ciudad y fecha en letra
   ├── Para / De / Entidad / Asunto / Prioridad
   └── Línea separadora

4. Cuerpo del documento
   └── Párrafos del contenido (separados por línea en blanco)

5. Firma
   ├── Línea horizontal
   ├── Nombre del firmante
   ├── Cargo
   └── Nombre de la entidad

6. Pie de página
   ├── Línea dorada
   └── Nombre CER | NIT | Ciudad | Radicado | Ley 594 de 2000
```

---

## 7. NOTIFICACIONES POR EMAIL

### 7.1 Configuración

El sistema usa Gmail con contraseña de aplicación:

```python
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
```

### 7.2 Eventos que generan notificación

| Evento | Función | Destinatarios |
|---|---|---|
| Nuevo documento radicado | `notificar_nuevo_documento()` | Responsable + Admins |
| Cambio de estado | `notificar_cambio_estado()` | Responsable + Radicado por |
| Documento próximo a vencer | `notificar_documento_vencido()` | Responsable + Admins |

### 7.3 Manejo de errores

Las notificaciones nunca rompen el flujo principal. Si falla el email, se registra en consola y el sistema continúa:

```python
try:
    send_mail(...)
except Exception as e:
    print(f'[CER Email Error] {e}')
```

---

## 8. REPORTES Y EXPORTACIÓN EXCEL

### 8.1 Estructura del Excel generado

**Hoja 1: Correspondencia {año}**
- Fila 1: Título institucional (fondo verde oscuro)
- Fila 2: Subtítulo con período
- Fila 3: Fecha de generación y referencia legal
- Fila 5: Encabezados de columnas
- Filas 6+: Datos de documentos con formato condicional por estado/prioridad

**Columnas:** N°, Radicado, Tipo, Flujo, Asunto, Remitente, Destinatario, Entidad, Estado, Prioridad, Fecha Radicación, Fecha Límite

**Hoja 2: Resumen**
- Estadísticas agrupadas por: Estado, Tipo, Flujo, Prioridad

### 8.2 Colores en Excel

| Estado | Color de fondo |
|---|---|
| Recibido | Azul claro #DBEAFE |
| En Trámite | Amarillo claro #FEF3C7 |
| Respondido | Verde claro #D1FAE5 |
| Archivado | Gris claro #F3F4F6 |

---

## 9. DESPLIEGUE EN RENDER

### 9.1 Archivos de configuración

**render.yaml:**
```yaml
services:
  - type: web
    name: cer-correspondencia
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
    startCommand: gunicorn config.wsgi:application
```

**Procfile:**
```
web: gunicorn config.wsgi:application
```

### 9.2 Variables de entorno en Render

Configurar en el dashboard de Render → Environment:

```
SECRET_KEY          = (clave segura generada)
DEBUG               = False
ALLOWED_HOSTS       = tu-app.onrender.com
EMAIL_HOST_USER     = swbas19@gmail.com
EMAIL_HOST_PASSWORD = (clave de aplicación Gmail)
```

### 9.3 Comando de alertas como Cron Job en Render

En Render → Cron Jobs:
- **Command:** `python manage.py verificar_vencimientos`
- **Schedule:** `0 7 * * *` (todos los días a las 7am)

---

## 10. ESTRUCTURA DE ARCHIVOS MEDIA (TRD - Ley 594/2000)

Los archivos digitales se organizan según los lineamientos de Tabla de Retención Documental:

```
media/
├── documentos/
│   ├── 2026/
│   │   ├── entrada/
│   │   │   ├── OF/
│   │   │   ├── MM/
│   │   │   ├── CR/
│   │   │   ├── RS/
│   │   │   └── AC/
│   │   └── salida/
│   │       └── (misma estructura)
│   └── 2027/
│       └── ...
├── plantillas/
│   └── generados/          ← PDFs generados
├── firmas/                 ← Firmas digitales de usuarios
└── membretes/              ← Membretes institucionales
```

---

## 11. GUÍA DE USO RÁPIDO

### Para el Administrador

1. **Crear usuarios:** Admin Django → Usuarios → Añadir → asignar rol
2. **Radicar documento:** Sidebar → Radicar documento → completar formulario
3. **Gestionar plantillas:** Sidebar → Plantillas CER → Editar plantilla
4. **Ver reportes:** Sidebar → Reportes → seleccionar período → Exportar Excel

### Para el Director

1. **Revisar bandeja:** Dashboard → documentos recientes y urgentes
2. **Cambiar estado:** Detalle del documento → sección "Cambiar estado"
3. **Generar PDF:** Detalle del documento → botón "Generar PDF"

### Para el Usuario Consulta

1. **Buscar documento:** Todos los documentos → campo de búsqueda
2. **Ver detalle:** Clic en el número de radicado
3. **Filtrar:** Usar filtros de tipo, estado, prioridad o fechas

---

## 12. MANTENIMIENTO

### Backup de la base de datos

```bash
cp db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3
```

### Actualizar dependencias

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Limpiar archivos de caché

```bash
find . -type d -name __pycache__ -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null
```

### Verificar vencimientos manualmente

```bash
python manage.py verificar_vencimientos
```

---

## 13. REGISTRO DE VERSIONES

| Versión | Fecha | Descripción |
|---|---|---|
| 1.0.0 | Feb 2026 | Versión inicial — sistema completo en producción |

---

## 14. CONTACTO Y SOPORTE

**Centro de Estudios Regionales — CER**
Desarrollo territorial · Mercado laboral · Políticas públicas

Repositorio: https://github.com/SwbasAprende/cer-correspondencia

---

*Documentación generada para la versión 1.0.0 del Sistema de Correspondencia Institucional CER.*
*Cumple con la Ley 594 de 2000 — Archivo General de la Nación de Colombia.*
