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
            'nombre', 'codigo', 'descripcion', 'duracion_anios',
            'titulo_otorgado', 'modalidad', 'activa'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre completo de la carrera',
                'maxlength': '150'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: TDS, TAS, etc.',
                'maxlength': '10',
                'style': 'text-transform: uppercase;'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada de la carrera, objetivos y perfil profesional'
            }),
            'duracion_anios': forms.Select(
                choices=[(i, f'{i} año{"s" if i > 1 else ""}') for i in range(1, 11)],
                attrs={'class': 'form-select'}
            ),
            'titulo_otorgado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Técnico Superior en...',
                'maxlength': '200'
            }),
            'modalidad': forms.Select(attrs={
                'class': 'form-select'
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

    def clean_codigo(self):
        """Validación personalizada para el código"""
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper().strip()
            
            # Verificar que no exista otro código igual (excepto la instancia actual)
            queryset = Carrera.objects.filter(codigo=codigo)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError('Ya existe una carrera con este código.')
                
            # Verificar formato del código (solo letras y números)
            if not codigo.replace('_', '').replace('-', '').isalnum():
                raise ValidationError('El código solo puede contener letras, números, guiones y guiones bajos.')
                
        return codigo

    def clean_nombre(self):
        """Validación personalizada para el nombre"""
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

    def clean_duracion_anios(self):
        """Validación de la duración en años"""
        duracion = self.cleaned_data.get('duracion_anios')
        
        if duracion:
            if duracion < 1:
                raise ValidationError('La duración debe ser al menos 1 año.')
            elif duracion > 10:
                raise ValidationError('La duración no puede ser mayor a 10 años.')
                
        return duracion

    def clean_titulo_otorgado(self):
        """Validación del título otorgado"""
        titulo = self.cleaned_data.get('titulo_otorgado')
        
        if titulo:
            titulo = titulo.strip()
            if len(titulo) < 10:
                raise ValidationError('El título debe tener al menos 10 caracteres.')
                
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
        choices=[('', 'Todas las duraciones')] + [(i, f'{i} año{"s" if i > 1 else ""}') for i in range(1, 11)],
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