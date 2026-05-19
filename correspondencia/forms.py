from django import forms
from .models import Documento
from .validators import validar_archivo_documento


class DocumentoForm(forms.ModelForm):

    class Meta:
        model  = Documento
        fields = [
            'tipo', 'flujo', 'prioridad', 'actor',
            'remitente', 'destinatario', 'entidad',
            'asunto', 'descripcion',
            'fecha_documento', 'responsable',
            'documento_referencia', 'archivo',
        ]
        widgets = {
            'tipo':      forms.Select(attrs={'class': 'cer-input'}),
            'flujo':     forms.Select(attrs={'class': 'cer-input'}),
            'prioridad': forms.Select(attrs={'class': 'cer-input'}),
            'actor':     forms.Select(attrs={'class': 'cer-input'}),
            'remitente':    forms.TextInput(attrs={'class': 'cer-input', 'placeholder': 'Nombre completo del remitente'}),
            'destinatario': forms.TextInput(attrs={'class': 'cer-input', 'placeholder': 'Nombre completo del destinatario'}),
            'entidad':      forms.TextInput(attrs={'class': 'cer-input', 'placeholder': 'Organización o entidad del remitente'}),
            'asunto':       forms.TextInput(attrs={'class': 'cer-input', 'placeholder': 'Asunto del documento'}),
            'descripcion':  forms.Textarea(attrs={'class': 'cer-input', 'rows': 4, 'placeholder': 'Observaciones adicionales (opcional)'}),
            'fecha_documento': forms.DateInput(attrs={'class': 'cer-input', 'type': 'date'}),
            'responsable':           forms.Select(attrs={'class': 'cer-input'}),
            'documento_referencia':  forms.Select(attrs={'class': 'cer-input'}),
        }
        labels = {
            'tipo':      'Tipo de documento',
            'flujo':     'Flujo',
            'prioridad': 'Prioridad',
            'actor':     'Actor del ecosistema CER',
            'remitente':    'Remitente',
            'destinatario': 'Destinatario',
            'entidad':      'Entidad / Organización',
            'asunto':       'Asunto',
            'descripcion':  'Descripción / Observaciones',
            'fecha_documento':       'Fecha del documento original',
            'responsable':           'Responsable asignado',
            'documento_referencia':  'En respuesta a (opcional)',
            'archivo':               'Archivo digital (PDF, DOCX, XLSX, JPG, PNG)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer opcionales los campos no obligatorios
        self.fields['descripcion'].required        = False
        self.fields['entidad'].required            = False
        self.fields['fecha_documento'].required    = False
        self.fields['responsable'].required        = False
        self.fields['documento_referencia'].required = False
        self.fields['archivo'].required            = False
        # Agregrar validador al campo archivo
        self.fields['archivo'].validators = [validar_archivo_documento]
        # Etiqueta amigable para referencia
        self.fields['documento_referencia'].queryset = Documento.objects.all().order_by('-fecha_radicacion')
        self.fields['documento_referencia'].empty_label = '— No es respuesta a otro documento —'
        self.fields['responsable'].empty_label = '— Sin asignar —'
    
    def clean_archivo(self):
        """
        Validación personalizada del campo archivo.
        Se ejecuta automáticamente cuando se valida el formulario.
        """
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # La validación de MIME type se hace en validar_archivo_documento()
            # Este método solo agrega validaciones adicionales si es necesario
            validar_archivo_documento(archivo)
        return archivo