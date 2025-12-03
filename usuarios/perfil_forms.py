from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from datetime import date, datetime
import re

Usuario = get_user_model()


class PerfilUpdateForm(forms.ModelForm):
    """
    Formulario personalizado para actualizar el perfil del usuario
    con validaciones completas y permisos según el rol
    """
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'dni', 'telefono', 'fecha_nacimiento', 'direccion']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tu nombre',
                'maxlength': '30'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tu apellido',
                'maxlength': '30'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678',
                'maxlength': '8',
                'pattern': '[0-9]{7,8}'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+54 11 1234-5678',
                'maxlength': '20'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tu dirección completa (mínimo 3 caracteres)',
                'rows': 2
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si el usuario NO es administrador, deshabilitar campos que no puede editar
        if self.instance and self.instance.rol != 'administrador':
            # Solo puede editar: teléfono, email y dirección
            campos_readonly = ['first_name', 'last_name', 'dni', 'fecha_nacimiento']
            
            for campo in campos_readonly:
                if campo in self.fields:
                    self.fields[campo].disabled = True
                    self.fields[campo].widget.attrs['readonly'] = 'readonly'
                    self.fields[campo].widget.attrs['class'] += ' bg-light'
                    self.fields[campo].help_text = 'Este campo solo puede ser modificado por un administrador'

    def clean_first_name(self):
        """Validar nombre"""
        first_name = self.cleaned_data.get('first_name', '').strip()
        
        if not first_name:
            raise ValidationError('El nombre es obligatorio.')
        
        if len(first_name) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', first_name):
            raise ValidationError('El nombre solo puede contener letras y espacios.')
        
        return first_name.title()  # Capitalizar primera letra

    def clean_last_name(self):
        """Validar apellido"""
        last_name = self.cleaned_data.get('last_name', '').strip()
        
        if not last_name:
            raise ValidationError('El apellido es obligatorio.')
        
        if len(last_name) < 2:
            raise ValidationError('El apellido debe tener al menos 2 caracteres.')
        
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', last_name):
            raise ValidationError('El apellido solo puede contener letras y espacios.')
        
        return last_name.title()  # Capitalizar primera letra

    def clean_email(self):
        """Validar email único"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError('El email es obligatorio.')
        
        # Verificar que sea único (excluyendo el usuario actual)
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe un usuario con este email.')
        
        return email

    def clean_dni(self):
        """Validar DNI"""
        dni = self.cleaned_data.get('dni', '').strip()
        
        if not dni:
            raise ValidationError('El DNI es obligatorio.')
        
        # Validar formato numérico
        if not dni.isdigit():
            raise ValidationError('El DNI debe contener solo números.')
        
        # Validar longitud
        if len(dni) < 7 or len(dni) > 8:
            raise ValidationError('El DNI debe tener 7 u 8 dígitos.')
        
        # Verificar que sea único (excluyendo el usuario actual)
        if Usuario.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe un usuario con este DNI.')
        
        return dni

    def clean_telefono(self):
        """Validar teléfono"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        if telefono:  # El teléfono es opcional
            # Permitir números, espacios, guiones, paréntesis y el símbolo +
            if not re.match(r'^[\d\s\-\+\(\)]+$', telefono):
                raise ValidationError('Formato de teléfono inválido. Use solo números, espacios, guiones, paréntesis y +.')
            
            # Verificar que tenga al menos 8 dígitos
            numeros = re.sub(r'[^\d]', '', telefono)
            if len(numeros) < 8:
                raise ValidationError('El teléfono debe tener al menos 8 dígitos.')
            
            if len(numeros) > 15:
                raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
        
        return telefono

    def clean_fecha_nacimiento(self):
        """Validar fecha de nacimiento"""
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if fecha_nacimiento:  # Es opcional
            hoy = date.today()
            
            # No puede ser en el futuro
            if fecha_nacimiento > hoy:
                raise ValidationError('La fecha de nacimiento no puede ser en el futuro.')
            
            # Calcular edad
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            
            # Validar edad razonable
            if edad < 16:
                raise ValidationError('Debes tener al menos 16 años.')
            
            if edad > 100:
                raise ValidationError('Por favor, verifica tu fecha de nacimiento.')
        
        return fecha_nacimiento

    def clean_direccion(self):
        """Validar dirección"""
        direccion = self.cleaned_data.get('direccion', '').strip()
        
        if direccion:  # Es opcional
            if len(direccion) < 3:
                raise ValidationError('La dirección debe tener al menos 3 caracteres.')
            
            # Permitir solo letras, números, espacios y algunos caracteres especiales comunes en direcciones
            if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\.,\-#°]+$', direccion):
                raise ValidationError('La dirección solo puede contener letras, números, espacios y los caracteres: . , - # °')
        
        return direccion

    def clean(self):
        """Validaciones adicionales que requieren múltiples campos"""
        cleaned_data = super().clean()
        
        first_name = cleaned_data.get('first_name', '')
        last_name = cleaned_data.get('last_name', '')
        
        # Verificar que nombre y apellido no sean iguales
        if first_name and last_name and first_name.lower() == last_name.lower():
            raise ValidationError('El nombre y apellido no pueden ser iguales.')
        
        return cleaned_data
