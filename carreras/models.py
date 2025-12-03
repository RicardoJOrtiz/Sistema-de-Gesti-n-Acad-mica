from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class Carrera(models.Model):
    """
    Modelo para las carreras académicas
    """
    
    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('semipresencial', 'Semipresencial'),
    ]
    
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Nombre de la Carrera'
    )
    
    codigo = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Código'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    duracion_anios = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        verbose_name='Duración (años)'
    )
    
    titulo_otorgado = models.CharField(
        max_length=200,
        verbose_name='Título que Otorga'
    )
    
    modalidad = models.CharField(
        max_length=20,
        choices=MODALIDAD_CHOICES,
        default='presencial',
        verbose_name='Modalidad'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['nombre']
        
    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse('carreras:detalle', kwargs={'pk': self.pk})
    
    def get_materias_count(self):
        """Retorna la cantidad de materias de la carrera"""
        return self.materias.filter(activa=True).count()
    
    def get_alumnos_count(self):
        """Retorna la cantidad de alumnos inscriptos en la carrera"""
        return self.alumnos_inscritos.filter(
            inscripcioncarrera__activa=True
        ).distinct().count()
    
    def puede_eliminarse(self):
        """Verifica si la carrera puede eliminarse (no tiene materias ni alumnos)"""
        return not (self.materias.exists() or self.alumnos_inscritos.exists())
