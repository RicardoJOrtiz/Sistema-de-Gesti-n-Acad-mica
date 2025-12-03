from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser
    Incluye campos adicionales para gestión académica
    """
    
    ROLES_CHOICES = [
        ('administrador', 'Administrador'),
        ('alumno', 'Alumno'),
        ('docente', 'Docente'),
        ('preceptor', 'Preceptor'),
        ('invitado', 'Invitado'),
    ]
    
    # Campos adicionales
    dni = models.CharField(
        max_length=8,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\d{7,8}$',
            message='El DNI debe tener 7 u 8 dígitos numéricos.'
        )],
        verbose_name='DNI'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)]+$',
            message='Formato de teléfono inválido.'
        )],
        verbose_name='Teléfono'
    )
    
    rol = models.CharField(
        max_length=15,
        choices=ROLES_CHOICES,
        default='invitado',
        verbose_name='Rol'
    )
    
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Nacimiento'
    )
    
    direccion = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )
    
    debe_cambiar_password = models.BooleanField(
        default=True,
        verbose_name='Debe cambiar contraseña'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    # Configuración del modelo
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.dni})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_rol_display_color(self):
        """Retorna el color Bootstrap para el rol"""
        colors = {
            'administrador': 'danger',
            'alumno': 'primary',
            'docente': 'success',
            'preceptor': 'warning',
            'invitado': 'secondary',
        }
        return colors.get(self.rol, 'secondary')
    
    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'administrador'
    
    def es_alumno(self):
        """Verifica si el usuario es alumno"""
        return self.rol == 'alumno'
    
    def es_docente(self):
        """Verifica si el usuario es docente"""
        return self.rol == 'docente'
    
    def es_preceptor(self):
        """Verifica si el usuario es preceptor"""
        return self.rol == 'preceptor'
    
    def puede_gestionar_usuarios(self):
        """Verifica si el usuario puede gestionar otros usuarios"""
        return self.rol == 'administrador'
    
    def puede_ver_inscripciones(self):
        """Verifica si el usuario puede ver inscripciones"""
        return self.rol in ['administrador', 'preceptor', 'docente']
    
    def puede_inscribirse(self):
        """Verifica si el usuario puede inscribirse a materias"""
        return self.rol == 'alumno'


class PerfilUsuario(models.Model):
    """
    Modelo para información adicional del perfil de usuario
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    
    foto = models.ImageField(
        upload_to='perfiles/',
        blank=True,
        null=True,
        verbose_name='Foto de Perfil'
    )
    
    biografia = models.TextField(
        blank=True,
        verbose_name='Biografía'
    )
    
    sitio_web = models.URLField(
        blank=True,
        verbose_name='Sitio Web'
    )
    
    linkedin = models.URLField(
        blank=True,
        verbose_name='LinkedIn'
    )
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"Perfil de {self.usuario.get_full_name()}"
