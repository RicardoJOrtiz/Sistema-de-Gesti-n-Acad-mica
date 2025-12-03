from django import forms
from django.core.exceptions import ValidationError
from .models import Materia
from carreras.models import Carrera
from unidecode import unidecode


class MateriaForm(forms.ModelForm):
    """
    Formulario para crear y editar materias
    """
    
    class Meta:
        model = Materia
        fields = [
            'nombre', 'carrera', 'descripcion', 
            'anio_cursado', 'cuatrimestre', 'carga_horaria', 
            'cupo_maximo', 'activa'
        ]
        labels = {
            'cuatrimestre': 'Modalidad',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la materia',
                'maxlength': '150',
                'required': 'required',
                'minlength': '3'
            }),
            'carrera': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada de la materia, contenidos y objetivos'
            }),
            'anio_cursado': forms.Select(
                choices=[(i, f'{i}° Año') for i in range(1, 6)],
                attrs={'class': 'form-select', 'required': 'required'}
            ),
            'cuatrimestre': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'carga_horaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '500',
                'placeholder': 'Horas totales',
                'required': 'required'
            }),
            'cupo_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': 'Cupo máximo de alumnos',
                'required': 'required'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar solo carreras activas
        self.fields['carrera'].queryset = Carrera.objects.filter(activa=True).order_by('nombre')
        self.fields['carrera'].empty_label = "Seleccionar carrera..."
        
        # Marcar campos como obligatorios
        self.fields['nombre'].required = True
        self.fields['carrera'].required = True
        self.fields['anio_cursado'].required = True
        self.fields['cuatrimestre'].required = True
        self.fields['carga_horaria'].required = True
        self.fields['cupo_maximo'].required = True
        self.fields['descripcion'].required = False  # Opcional
        
        # Establecer valores por defecto
        if not self.instance.pk:  # Solo para nuevas materias
            self.fields['cupo_maximo'].initial = 30
            self.fields['activa'].initial = True

    def generar_codigo(self, nombre, carrera):
        """
        Genera un código único para la materia basado en el nombre y la carrera
        """
        # Normalizar el nombre (quitar acentos y convertir a mayúsculas)
        nombre_normalizado = unidecode(nombre).upper()
        
        # Tomar las primeras 3 letras del nombre
        prefijo_nombre = ''.join(filter(str.isalpha, nombre_normalizado))[:3]
        
        # Tomar las primeras 2 letras del código de la carrera
        prefijo_carrera = carrera.codigo[:2] if len(carrera.codigo) >= 2 else carrera.codigo
        
        # Combinar prefijos
        base_codigo = f"{prefijo_carrera}{prefijo_nombre}"
        
        # Intentar generar código único con contador
        contador = 1
        codigo = f"{base_codigo}{contador:02d}"
        
        # Buscar código disponible
        while Materia.objects.filter(codigo=codigo).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            contador += 1
            if contador > 999:
                # Si llegamos a 999, usar timestamp
                from datetime import datetime
                codigo = f"{base_codigo}{datetime.now().strftime('%H%M%S')}"
                break
            codigo = f"{base_codigo}{contador:02d}"
        
        return codigo

    def clean_nombre(self):
        """Validación personalizada para el nombre"""
        nombre = self.cleaned_data.get('nombre')
        carrera = self.cleaned_data.get('carrera')
        
        if nombre:
            nombre = nombre.strip()
            
            # Validar longitud mínima
            if len(nombre) < 3:
                raise ValidationError('El nombre debe tener al menos 3 caracteres.')
            
            if len(nombre) > 150:
                raise ValidationError('El nombre no puede exceder los 150 caracteres.')
            
            # Verificar que no exista otra materia con el mismo nombre en la misma carrera
            if carrera:
                queryset = Materia.objects.filter(nombre__iexact=nombre, carrera=carrera)
                if self.instance.pk:
                    queryset = queryset.exclude(pk=self.instance.pk)
                
                if queryset.exists():
                    raise ValidationError(f'Ya existe una materia con el nombre "{nombre}" en la carrera {carrera.nombre}.')
        else:
            raise ValidationError('El nombre de la materia es obligatorio.')
                
        return nombre

    def clean_cupo_maximo(self):
        """Validación del cupo máximo"""
        cupo_maximo = self.cleaned_data.get('cupo_maximo')
        
        if cupo_maximo:
            if cupo_maximo < 1:
                raise ValidationError('El cupo máximo debe ser al menos 1.')
            elif cupo_maximo > 100:
                raise ValidationError('El cupo máximo no puede ser mayor a 100.')
            
            # Si es una materia existente, verificar que el nuevo cupo no sea menor a los inscriptos actuales
            if self.instance.pk:
                inscriptos_actuales = self.instance.get_inscriptos_count()
                if cupo_maximo < inscriptos_actuales:
                    raise ValidationError(
                        f'El cupo máximo no puede ser menor a {inscriptos_actuales} '
                        f'(cantidad actual de inscriptos).'
                    )
                    
        return cupo_maximo

    def clean_carga_horaria(self):
        """Validación de la carga horaria"""
        carga_horaria = self.cleaned_data.get('carga_horaria')
        
        if carga_horaria:
            if carga_horaria < 1:
                raise ValidationError('La carga horaria debe ser al menos 1 hora.')
            elif carga_horaria > 500:
                raise ValidationError('La carga horaria no puede ser mayor a 500 horas.')
                
        return carga_horaria

    def clean(self):
        """Validaciones que requieren múltiples campos"""
        cleaned_data = super().clean()
        carrera = cleaned_data.get('carrera')
        anio_cursado = cleaned_data.get('anio_cursado')
        
        if carrera and anio_cursado:
            # Verificar que el año no sea mayor a la duración de la carrera
            if anio_cursado > carrera.duracion_anios:
                raise ValidationError({
                    'anio_cursado': f'El año de cursado no puede ser mayor a {carrera.duracion_anios} '
                                   f'(duración de la carrera {carrera.nombre}).'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        """Sobrescribir save para generar el código automáticamente"""
        instance = super().save(commit=False)
        
        # Generar código automáticamente si es una nueva materia
        if not instance.pk:
            nombre = self.cleaned_data.get('nombre')
            carrera = self.cleaned_data.get('carrera')
            if nombre and carrera:
                instance.codigo = self.generar_codigo(nombre, carrera)
        
        if commit:
            instance.save()
        
        return instance


class FiltroMateriaForm(forms.Form):
    """
    Formulario para filtrar materias en la lista
    """
    carrera = forms.ModelChoiceField(
        queryset=Carrera.objects.filter(activa=True).order_by('nombre'),
        required=False,
        empty_label="Todas las carreras",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    anio = forms.ChoiceField(
        choices=[('', 'Todos los años')] + [(i, f'{i}° Año') for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    cuatrimestre = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', '1° Cuatrimestre'),
            ('2', '2° Cuatrimestre'),
            ('0', 'Anual'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    con_cupo = forms.BooleanField(
        required=False,
        label='Solo con cupo disponible',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    buscar = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o código...'
        })
    )


class InscripcionMateriaForm(forms.Form):
    """
    Formulario simple para inscribirse a una materia
    """
    confirmar = forms.BooleanField(
        required=True,
        label='Confirmo que deseo inscribirme a esta materia',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': True
        })
    )
    
    observaciones = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones opcionales sobre la inscripción'
        })
    )