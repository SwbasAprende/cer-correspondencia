# 📄 Sistema de Correspondencia Institucional — CER

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2.9-092E20?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

**Sistema de gestión de correspondencia institucional para el Centro de Estudios Regionales (CER)**

*Cumple con la Ley 594 de 2000 — Archivo General de la Nación de Colombia*

</div>

---

## 📋 Descripción

El Sistema de Correspondencia Institucional del CER es una aplicación web desarrollada en Django que permite gestionar de forma integral toda la correspondencia del Centro de Estudios Regionales. Desde la radicación automática de documentos hasta la generación de PDFs con membrete institucional, pasando por el seguimiento de estados, trazabilidad completa y reportes estadísticos.

Diseñado para un volumen bajo-medio de documentos (5-30 mensuales), priorizando la simplicidad operativa y el cumplimiento normativo colombiano.

---

## ✨ Funcionalidades

### 📥 Radicación de Documentos
- Consecutivo automático por año y tipo: `CER-OF-2026-001`
- Registro de fecha **y hora exacta** de radicación
- Soporte para 5 tipos: Oficio, Memorando, Circular, Resolución, Acta
- Flujo de entrada y salida
- Carga de archivo digital (PDF, JPG, PNG)

### 📊 Dashboard
- Estadísticas en tiempo real
- Documentos urgentes con alertas de vencimiento
- Acceso rápido a documentos recientes

### 🔍 Búsqueda y Filtros
- Búsqueda por radicado, asunto, remitente o destinatario
- Filtros por estado, tipo, prioridad, flujo y rango de fechas
- Indicadores visuales de documentos vencidos o próximos a vencer

### 📜 Trazabilidad (Ley 594/2000)
- Historial completo de cambios de estado
- Registro de usuario, fecha, hora y observación por cada cambio
- Estados: Recibido → En Trámite → Respondido → Archivado

### 📄 Plantillas Institucionales con PDF
- Plantillas editables para cada tipo de documento
- Generador de PDF con membrete institucional, logo y firma
- Incluye radicado, fecha, hora, destinatario y pie de página legal
- Registro de todos los PDFs generados

### 📈 Reportes y Excel
- Resumen estadístico por estado, tipo, flujo y prioridad
- Exportación a Excel con dos hojas: detalle y resumen
- Filtro por año y mes
- Formato profesional con colores institucionales

### 🔐 Roles y Permisos
| Función | Administrador | Director | Consulta |
|---|:---:|:---:|:---:|
| Radicar documentos | ✅ | ✅ | ❌ |
| Cambiar estado | ✅ | ✅ | ❌ |
| Ver confidenciales | ✅ | ✅ | ❌ |
| Generar PDF | ✅ | ✅ | ❌ |
| Gestionar usuarios | ✅ | ❌ | ❌ |
| Exportar reportes | ✅ | ✅ | ❌ |
| Buscar y consultar | ✅ | ✅ | ✅ |

### 📧 Notificaciones por Email
- Notificación automática al radicar un documento
- Alerta de cambio de estado
- Alerta de documentos próximos a vencer (1 día)

### 🖨️ Sticker de Radicado
- Etiqueta imprimible con número de radicado, fecha y hora
- Se abre en ventana de impresión directamente desde el sistema

---

## 🗂️ Ecosistema de Actores CER

El sistema clasifica la correspondencia según los actores del ecosistema:

- Gremios
- Agroindustrias
- Cooperativas de producción
- Instituciones educativas
- Cámara de Comercio
- DIAN
- Entidades públicas territoriales
- Sector privado
- Interno CER

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.12 + Django 4.2.9 |
| Base de datos | SQLite 3 |
| Frontend | HTML5 + CSS3 (diseño propio institucional) |
| Generación PDF | ReportLab 4.4 |
| Exportación Excel | OpenPyXL |
| Autenticación | Django Auth + roles personalizados |
| Variables de entorno | python-decouple + python-dotenv |
| Servidor de producción | Gunicorn |
| Archivos estáticos | WhiteNoise |
| Despliegue | Render |

---

## 📁 Estructura del Proyecto

```
cer-correspondencia/
├── config/                         # Configuración principal Django
│   ├── settings.py                 # Configuración del proyecto
│   ├── urls.py                     # URLs principales
│   ├── wsgi.py                     # Servidor WSGI
│   └── context_processors.py      # Contexto global (CER_VERSION, año)
│
├── correspondencia/                # App principal — documentos
│   ├── models.py                   # Documento, Trazabilidad
│   ├── views.py                    # Vistas CRUD de documentos
│   ├── forms.py                    # Formulario de radicación
│   ├── urls.py                     # URLs de correspondencia
│   ├── admin.py                    # Panel de administración
│   ├── notificaciones.py           # Envío de emails automáticos
│   └── management/
│       └── commands/
│           └── verificar_vencimientos.py  # Comando para alertas
│
├── usuarios/                       # App de autenticación y roles
│   ├── models.py                   # Usuario personalizado con roles
│   ├── views.py                    # Login, perfil, cambio de contraseña
│   ├── urls.py                     # URLs de usuarios
│   └── admin.py                    # Gestión en panel admin
│
├── plantillas/                     # App de plantillas institucionales
│   ├── models.py                   # PlantillaDocumento, DocumentoGenerado
│   ├── views.py                    # Editor y generador de PDF
│   ├── urls.py                     # URLs de plantillas
│   ├── admin.py                    # Panel admin
│   └── generador_pdf.py            # Motor de generación PDF con ReportLab
│
├── reportes/                       # App de reportes y estadísticas
│   ├── views.py                    # Reportes y exportación Excel
│   └── urls.py                     # URLs de reportes
│
├── static/
│   ├── css/
│   │   └── cer.css                 # Estilos institucionales CER
│   └── img/
│       └── logo-cer.png            # Logo institucional
│
├── templates/
│   ├── base/
│   │   ├── base.html               # Layout principal con sidebar
│   │   └── dashboard.html          # Dashboard principal
│   ├── correspondencia/            # Templates de documentos
│   ├── usuarios/                   # Templates de autenticación
│   ├── plantillas/                 # Templates de plantillas/PDF
│   └── reportes/                   # Templates de reportes
│
├── media/                          # Archivos subidos (no en Git)
├── .env                            # Variables de entorno (no en Git)
├── .gitignore
├── manage.py
├── requirements.txt
├── Procfile                        # Para Railway
└── render.yaml                     # Para Render
```

---

## 🚀 Instalación Local

### Requisitos previos
- Python 3.10+
- Git

### Pasos

**1. Clonar el repositorio**
```bash
git clone https://github.com/SwbasAprende/cer-correspondencia.git
cd cer-correspondencia
```

**2. Crear y activar el entorno virtual**
```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

**3. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**4. Crear el archivo `.env`**
```bash
cp .env.example .env
```
Edita `.env` con tus valores:
```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=*
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-clave-de-aplicacion
```

**5. Aplicar migraciones**
```bash
python manage.py migrate
```

**6. Crear superusuario**
```bash
python manage.py createsuperuser
```

**7. Arrancar el servidor**
```bash
python manage.py runserver
```

Visita **http://127.0.0.1:8000** y accede con el usuario creado.

---

## ⚙️ Variables de Entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta Django | `django-insecure-...` |
| `DEBUG` | Modo debug | `True` / `False` |
| `ALLOWED_HOSTS` | Hosts permitidos | `*` / `tudominio.com` |
| `EMAIL_HOST_USER` | Email remitente | `sistema@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Contraseña de app Gmail | `xxxx xxxx xxxx xxxx` |

---

## 📧 Configurar Notificaciones por Email

1. Ve a **https://myaccount.google.com/apppasswords**
2. Crea una contraseña de aplicación con nombre `CER Sistema`
3. Copia la clave de 16 caracteres en `EMAIL_HOST_PASSWORD` del `.env`

Para probar:
```bash
python manage.py shell -c "
from django.core.mail import send_mail
send_mail('[CER] Prueba', 'Test OK', None, ['tu@email.com'])
print('OK')
"
```

---

## ⏰ Alertas de Vencimiento (Cron)

Para recibir alertas diarias de documentos próximos a vencer, configura una tarea programada que ejecute:

```bash
python manage.py verificar_vencimientos
```

En Render puedes configurarlo como un **Cron Job** en el dashboard.

---

## 📐 Modelo de Radicado

Los números de radicado siguen esta estructura:

```
CER - [TIPO] - [AÑO] - [CONSECUTIVO]

CER-OF-2026-001   → Oficio #1 del año 2026
CER-MM-2026-003   → Memorando #3 del año 2026
CER-CR-2026-001   → Circular #1 del año 2026
CER-RS-2026-002   → Resolución #2 del año 2026
CER-AC-2026-001   → Acta #1 del año 2026
```

El consecutivo se reinicia cada año por tipo de documento.

---

## ⚖️ Cumplimiento Normativo

Este sistema está diseñado para cumplir con:

- **Ley 594 de 2000** — Ley General de Archivos de Colombia
- **Lineamientos del Archivo General de la Nación**
- **Tabla de Retención Documental (TRD)**: archivos organizados por año/tipo/flujo
- **Trazabilidad completa**: todo cambio queda registrado con usuario, fecha y hora
- **Retención documental**: estructura de carpetas compatible con TRD institucional

---

## 🤝 Contribuir

Este proyecto es de uso institucional del CER. Para reportar errores o sugerir mejoras, abre un [Issue](https://github.com/SwbasAprende/cer-correspondencia/issues).

---

## 📄 Licencia

Uso exclusivo del Centro de Estudios Regionales — CER.

---

<div align="center">
  <strong>Centro de Estudios Regionales — CER</strong><br>
  Desarrollo territorial · Mercado laboral · Políticas públicas<br>
  <em>Sistema desarrollado con Django · Ley 594 de 2000</em>
</div>
