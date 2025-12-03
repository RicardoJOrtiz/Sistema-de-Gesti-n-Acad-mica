from django import forms
from django.core.exceptions import ValidationError
from .models import Carrera


class CarreraForm(forms.ModelForm):
    """
    Formulario para crear y editar carreras
    """
    
    class Meta:
        model = Carrera
        fields = [
            'nombre', 'descripcion', 'duracion_anios',
            'titulo_otorgado', 'modalidad', 'activa'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre completo de la carrera',
                'maxlength': '150',
                'required': 'required',
                'minlength': '5'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada de la carrera, objetivos y perfil profesional',
                'minlength': '20'
            }),
            'duracion_anios': forms.Select(
                choices=[(i, f'{i} año{"s" if i > 1 else ""}') for i in range(1, 7)],
                attrs={'class': 'form-select', 'required': 'required'}
            ),
            'titulo_otorgado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Técnico Superior en...',
                'maxlength': '200',
                'required': 'required',
                'minlength': '10'
            }),
            'modalidad': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer valores por defecto para nuevas carreras
        if not self.instance.pk:
            self.fields['duracion_anios'].initial = 3
            self.fields['activa'].initial = True
            self.fields['modalidad'].initial = 'presencial'

    def generar_codigo(self, nombre):
        """Genera un código único a partir del nombre de la carrera"""
        import re
        from unidecode import unidecode
        
        # Convertir a ASCII (eliminar tildes)
        nombre_ascii = unidecode(nombre)
        
        # Extraer palabras significativas (mayores a 2 letras)
        palabras = re.findall(r'\b[a-zA-Z]{3,}\b', nombre_ascii)
        
        # Tomar las iniciales de las primeras palabras
        if len(palabras) >= 3:
            codigo_base = ''.join([p[0].upper() for p in palabras[:4]])
        elif len(palabras) == 2:
            codigo_base = palabras[0][:2].upper() + palabras[1][:2].upper()
        elif len(palabras) == 1:
            codigo_base = palabras[0][:4].upper()
        else:
            # Si no hay palabras válidas, usar las primeras letras del nombre
            codigo_base = re.sub(r'[^a-zA-Z]', '', nombre_ascii)[:4].upper()
        
        # Limitar el código base a máximo 8 caracteres para dejar espacio para el contador
        codigo_base = codigo_base[:8]
        
        # Asegurar que el código sea único
        codigo = codigo_base
        contador = 1
        max_intentos = 999  # Límite de seguridad
        
        while contador <= max_intentos:
            # Verificar si el código ya existe en la base de datos
            queryset = Carrera.objects.filter(codigo=codigo)
            
            # Excluir la instancia actual si estamos editando
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            # Si no existe, retornar este código
            if not queryset.exists():
                return codigo
            
            # Si ya existe, agregar un número y volver a intentar
            codigo = f"{codigo_base}{contador}"
            contador += 1
        
        # Si llegamos aquí, algo está mal (999 códigos duplicados)
        raise ValidationError(
            f'No se pudo generar un código único para la carrera "{nombre}". '
            'Por favor, contacte al administrador del sistema.'
        )


    def clean_nombre(self):
        """Validación personalizada para el nombre y generación automática del código"""
        nombre = self.cleaned_data.get('nombre')
        
        if nombre:
            nombre = nombre.strip()
            
            # Verificar que no exista otra carrera con el mismo nombre
            queryset = Carrera.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError(f'Ya existe una carrera con el nombre "{nombre}".')
        
        return nombre
    
    def save(self, commit=True):
        """Generar código automáticamente antes de guardar"""
        instance = super().save(commit=False)
        
        # Generar código solo si es una nueva carrera o si el nombre cambió
        if not instance.pk or 'nombre' in self.changed_data:
            instance.codigo = self.generar_codigo(instance.nombre)
        
        if commit:
            instance.save()
        
        return instance

    def clean_duracion_anios(self):
        """Validación de la duración en años"""
        duracion = self.cleaned_data.get('duracion_anios')
        
        if duracion:
            if duracion < 1:
                raise ValidationError('La duración debe ser al menos 1 año.')
            elif duracion > 6:
                raise ValidationError('La duración no puede ser mayor a 6 años.')
                
        return duracion

    def clean_descripcion(self):
        """Validación de la descripción"""
        descripcion = self.cleaned_data.get('descripcion')
        
        if descripcion:
            descripcion = descripcion.strip()
            if len(descripcion) < 20:
                raise ValidationError('La descripción debe tener al menos 20 caracteres para ser descriptiva.')
            if len(descripcion) > 2000:
                raise ValidationError('La descripción no puede exceder los 2000 caracteres.')
                
        return descripcion
    
    def clean_titulo_otorgado(self):
        """Validación del título otorgado"""
        titulo = self.cleaned_data.get('titulo_otorgado')
        
        if titulo:
            titulo = titulo.strip()
            if len(titulo) < 10:
                raise ValidationError('El título debe tener al menos 10 caracteres.')
            if len(titulo) > 200:
                raise ValidationError('El título no puede exceder los 200 caracteres.')
                
        return titulo


class FiltroCarreraForm(forms.Form):
    """
    Formulario para filtrar carreras en la lista
    """
    modalidad = forms.ChoiceField(
        choices=[('', 'Todas las modalidades')] + Carrera.MODALIDAD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    duracion = forms.ChoiceField(
        choices=[('', 'Todas las duraciones')] + [(i, f'{i} año{"s" if i > 1 else ""}') for i in range(1, 7)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    activa = forms.ChoiceField(
        choices=[
            ('', 'Todas'),
            ('True', 'Solo activas'),
            ('False', 'Solo inactivas'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    buscar = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o código...'
        })
    )