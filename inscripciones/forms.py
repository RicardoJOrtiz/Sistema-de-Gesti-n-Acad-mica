from django import forms
from .models import Inscripcion
from alumnos.models import Alumno
from materias.models import Materia


class InscripcionForm(forms.ModelForm):
    """Formulario para crear inscripciones"""
    
    class Meta:
        model = Inscripcion
        fields = ['alumno', 'materia']
        widgets = {
            'alumno': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_alumno'
            }),
            'materia': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_materia'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar queryset inicial
        self.fields['alumno'].queryset = Alumno.objects.select_related('usuario').filter(
            usuario__is_active=True
        ).order_by('usuario__first_name', 'usuario__last_name')
        
        # Inicialmente mostrar todas las materias activas
        self.fields['materia'].queryset = Materia.objects.select_related('carrera').filter(
            activa=True
        ).order_by('carrera__nombre', 'nombre')
        
        # Labels
        self.fields['alumno'].label = 'Alumno'
        self.fields['alumno'].empty_label = '---------'
        self.fields['materia'].label = 'Materia'
        self.fields['materia'].empty_label = 'Selecciona un alumno primero'
