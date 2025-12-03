from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import Usuario, PerfilUsuario


class CustomLoginForm(AuthenticationForm):
    """
    Formulario personalizado de login
    Permite login con DNI o email
    """
    username = forms.CharField(
        label='DNI o Email',
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su DNI o email',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )
    
    def clean_username(self):
        """Permite login con DNI o email"""
        username = self.cleaned_data.get('username')
        
        # Buscar usuario por DNI o email
        try:
            if '@' in username:
                # Es un email
                user = Usuario.objects.get(email=username)
            else:
                # Es un DNI
                user = Usuario.objects.get(dni=username)
            
            # Retornar el username real para la autenticación
            return user.username
            
        except Usuario.DoesNotExist:
            # Django manejará el error de autenticación
            pass
        
        return username


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario personalizado para cambio de contraseña
    """
    old_password = forms.CharField(
        label='Contraseña actual',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña actual'
        })
    )
    
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la nueva contraseña'
        }),
        help_text='La contraseña debe tener al menos 8 caracteres.'
    )
    
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme la nueva contraseña'
        })
    )


class UsuarioCreateForm(forms.ModelForm):
    """
    Formulario para crear usuarios
    Campos obligatorios: username, first_name, last_name, email, dni, rol
    Campos opcionales: telefono, fecha_nacimiento, direccion
    Si el rol es alumno, la carrera es obligatoria
    """
    
    # Definir campos explícitamente con validaciones
    username = forms.CharField(
        label='Usuario',
        required=True,
        min_length=4,
        max_length=30,
        validators=[RegexValidator(
            regex=r'^[a-zA-Z0-9_-]+$',
            message='El usuario solo puede contener letras, números, guiones y guiones bajos'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario123',
            'pattern': '[a-zA-Z0-9_-]{4,30}'
        }),
        help_text='Mínimo 4 caracteres. Solo letras, números, - y _'
    )
    
    first_name = forms.CharField(
        label='Nombre',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    
    last_name = forms.CharField(
        label='Apellido',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        })
    )
    
    email = forms.EmailField(
        label='Email',
        required=True,
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    
    dni = forms.CharField(
        label='DNI',
        required=True,
        validators=[RegexValidator(
            regex=r'^\d{7,8}$',
            message='El DNI debe contener solo números (7 u 8 dígitos)'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'maxlength': '8',
            'pattern': '[0-9]{7,8}'
        })
    )
    
    telefono = forms.CharField(
        label='Teléfono',
        required=True,
        validators=[RegexValidator(
            regex=r'^\+?[\d\s\-\(\)]{7,20}$',
            message='Formato de teléfono inválido. Ejemplo: +54 9 11 1234-5678'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+54 9 11 1234-5678'
        })
    )
    
    fecha_nacimiento = forms.DateField(
        label='Fecha de Nacimiento',
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    direccion = forms.CharField(
        label='Dirección',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Dirección completa (opcional)'
        })
    )
    
    # Campo para asignar carrera a alumnos
    carrera = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Carrera',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='Selecciona la carrera del alumno (obligatorio para alumnos)'
    )
    
    # Campo para asignar materias a docentes
    materias = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        label='Materias a cargo',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text='Selecciona las materias que este docente dictará (opcional)'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar todas las carreras activas
        from carreras.models import Carrera
        self.fields['carrera'].queryset = Carrera.objects.filter(activa=True).order_by('nombre')
        
        # Cargar todas las materias activas
        from materias.models import Materia
        self.fields['materias'].queryset = Materia.objects.filter(activa=True).order_by('carrera__nombre', 'anio_cursado', 'nombre')
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'dni',
            'telefono', 'rol', 'fecha_nacimiento', 'direccion'
        ]
        widgets = {
            'rol': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleRoleSpecificFields(this.value)'
            }),
        }
    
    def clean_fecha_nacimiento(self):
        """Validar que la fecha de nacimiento sea válida"""
        from datetime import date
        
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if not fecha_nacimiento:
            raise ValidationError('La fecha de nacimiento es obligatoria.')
        
        # Validar que no sea una fecha futura
        if fecha_nacimiento > date.today():
            raise ValidationError('La fecha de nacimiento no puede ser posterior a la fecha actual.')
        
        # Calcular la edad
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year
        # Ajustar si aún no cumplió años este año
        if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1
        
        # Validar edad: mayor a 17 y menor a 100 años
        if edad <= 17:
            raise ValidationError(
                f'El usuario debe tener más de 17 años. Edad actual: {edad} años.'
            )
        
        if edad >= 100:
            raise ValidationError(
                f'La edad no puede ser mayor o igual a 100 años. Edad actual: {edad} años.'
            )
        
        return fecha_nacimiento
    
    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        carrera = cleaned_data.get('carrera')
        telefono = cleaned_data.get('telefono')
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        
        # Si el rol es alumno, la carrera es obligatoria
        if rol == 'alumno' and not carrera:
            from carreras.models import Carrera
            if Carrera.objects.filter(activa=True).exists():
                raise ValidationError({
                    'carrera': 'Debe seleccionar una carrera para el alumno.'
                })
        
        # Para roles alumno, docente, preceptor: teléfono y fecha son obligatorios
        if rol in ['alumno', 'docente', 'preceptor']:
            if not telefono:
                raise ValidationError({
                    'telefono': 'El teléfono es obligatorio para este rol.'
                })
            if not fecha_nacimiento:
                raise ValidationError({
                    'fecha_nacimiento': 'La fecha de nacimiento es obligatoria para este rol.'
                })
        
        # Para rol invitado: teléfono y fecha son opcionales (ya se manejan con required=False dinámicamente)
        
        return cleaned_data
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este email.')
        return email
    
    def clean_dni(self):
        """Validar que el DNI sea único"""
        dni = self.cleaned_data.get('dni')
        if Usuario.objects.filter(dni=dni).exists():
            raise ValidationError('Ya existe un usuario con este DNI.')
        return dni
    
    def clean_username(self):
        """Validar que el username sea único"""
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError('Ya existe un usuario con este nombre de usuario.')
        return username


class UsuarioUpdateForm(forms.ModelForm):
    """
    Formulario para editar usuarios
    Aplica las mismas validaciones que el formulario de creación
    """
    
    # Campos con validaciones explícitas
    username = forms.CharField(
        label='Usuario',
        required=True,
        min_length=4,
        max_length=30,
        validators=[RegexValidator(
            regex=r'^[a-zA-Z0-9_-]+$',
            message='El usuario solo puede contener letras, números, guiones y guiones bajos'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario123',
            'pattern': '[a-zA-Z0-9_-]{4,30}'
        })
    )
    
    first_name = forms.CharField(
        label='Nombre',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        label='Apellido',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        label='Email',
        required=True,
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    dni = forms.CharField(
        label='DNI',
        required=True,
        validators=[RegexValidator(
            regex=r'^\d{7,8}$',
            message='El DNI debe contener solo números (7 u 8 dígitos)'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'maxlength': '8',
            'pattern': '[0-9]{7,8}'
        })
    )
    
    telefono = forms.CharField(
        label='Teléfono',
        required=True,
        validators=[RegexValidator(
            regex=r'^\+?[\d\s\-\(\)]{7,20}$',
            message='Formato de teléfono inválido. Ejemplo: +54 9 11 1234-5678'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+54 9 11 1234-5678'
        })
    )
    
    fecha_nacimiento = forms.DateField(
        label='Fecha de Nacimiento',
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    direccion = forms.CharField(
        label='Dirección',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Dirección completa (opcional)'
        })
    )
    
    # Campo para asignar materias a docentes
    materias = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        label='Materias a cargo',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text='Selecciona las materias que este docente dictará (opcional)'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si hay una instancia, formatear la fecha correctamente
        if self.instance and self.instance.pk and self.instance.fecha_nacimiento:
            self.initial['fecha_nacimiento'] = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')
        
        # Cargar todas las materias activas
        from materias.models import Materia
        self.fields['materias'].queryset = Materia.objects.filter(activa=True).order_by('carrera__nombre', 'anio_cursado', 'nombre')
        
        # Si es un docente existente, pre-seleccionar sus materias
        if self.instance and self.instance.pk and self.instance.rol == 'docente':
            self.initial['materias'] = Materia.objects.filter(docente=self.instance)
    
    class Meta:
        model = Usuario
        fields = [
            'username', 'first_name', 'last_name', 'email', 'dni',
            'telefono', 'rol', 'fecha_nacimiento', 'direccion', 'is_active'
        ]
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_username(self):
        """Validar que el username sea único (excepto el actual)"""
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe un usuario con este nombre de usuario.')
        return username
    
    def clean_dni(self):
        """Validar que el DNI sea único (excepto el actual)"""
        dni = self.cleaned_data.get('dni')
        if Usuario.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe un usuario con este DNI.')
        return dni
    
    def clean_email(self):
        """Validar que el email sea único (excepto el actual)"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe un usuario con este email.')
        return email
    
    def clean_fecha_nacimiento(self):
        """Validar fecha de nacimiento si se proporciona"""
        from datetime import date
        
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if not fecha_nacimiento:
            return fecha_nacimiento
        
        # Validar que no sea una fecha futura
        if fecha_nacimiento > date.today():
            raise ValidationError('La fecha de nacimiento no puede ser posterior a la fecha actual.')
        
        # Calcular la edad
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year
        if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1
        
        # Validar edad: mayor a 17 y menor a 100 años
        if edad <= 17:
            raise ValidationError(
                f'El usuario debe tener más de 17 años. Edad actual: {edad} años.'
            )
        
        if edad >= 100:
            raise ValidationError(
                f'La edad no puede ser mayor o igual a 100 años. Edad actual: {edad} años.'
            )
        
        return fecha_nacimiento


class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario
    """
    
    class Meta:
        model = PerfilUsuario
        fields = ['foto', 'biografia', 'sitio_web', 'linkedin']
        widgets = {
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'biografia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntanos sobre ti...'
            }),
            'sitio_web': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://mi-sitio.com'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/mi-perfil'
            }),
        }


class FiltroUsuariosForm(forms.Form):
    """
    Formulario para filtrar usuarios
    """
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, DNI o email...'
        })
    )
    
    rol = forms.ChoiceField(
        choices=[('', 'Todos los roles')] + Usuario.ROLES_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class RecuperarPasswordForm(forms.Form):
    """
    Formulario para solicitar recuperación de contraseña
    """
    email = forms.EmailField(
        label='Correo Electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su correo electrónico registrado',
            'autofocus': True
        }),
        help_text='Ingrese el correo electrónico asociado a su cuenta'
    )
    
    def clean_email(self):
        """Verificar que el email existe en el sistema"""
        email = self.cleaned_data.get('email')
        
        try:
            usuario = Usuario.objects.get(email=email, is_active=True)
        except Usuario.DoesNotExist:
            raise ValidationError(
                'No existe una cuenta activa asociada a este correo electrónico.'
            )
        
        return email


class RestablecerPasswordForm(forms.Form):
    """
    Formulario para establecer nueva contraseña
    """
    new_password1 = forms.CharField(
        label='Nueva Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nueva contraseña',
            'autocomplete': 'new-password'
        }),
        help_text='La contraseña debe tener al menos 8 caracteres'
    )
    
    new_password2 = forms.CharField(
        label='Confirmar Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su nueva contraseña',
            'autocomplete': 'new-password'
        })
    )
    
    def clean_new_password1(self):
        """Validar fortaleza de la contraseña"""
        password = self.cleaned_data.get('new_password1')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if password.isdigit():
            raise ValidationError('La contraseña no puede ser solo números.')
        
        if password.lower() in ['password', 'contraseña', '12345678']:
            raise ValidationError('La contraseña es demasiado común.')
        
        return password
    
    def clean_new_password2(self):
        """Verificar que las contraseñas coincidan"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return password2
