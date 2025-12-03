from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from carreras.models import Carrera


class Materia(models.Model):
    """
    Modelo para las materias de las carreras
    """
    
    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre de la Materia'
    )
    
    codigo = models.CharField(
        max_length=15,
        unique=True,
        verbose_name='Código'
    )
    
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.CASCADE,
        related_name='materias',
        verbose_name='Carrera'
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    anio_cursado = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Año de Cursado'
    )
    
    cuatrimestre = models.PositiveIntegerField(
        choices=[
            (1, 'Primer Cuatrimestre'),
            (2, 'Segundo Cuatrimestre'),
            (0, 'Anual'),
        ],
        default=1,
        verbose_name='Cuatrimestre'
    )
    
    carga_horaria = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(500)],
        verbose_name='Carga Horaria (horas)'
    )
    
    cupo_maximo = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Cupo Máximo'
    )
    
    docente = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'rol': 'docente'},
        related_name='materias_asignadas',
        verbose_name='Docente Asignado'
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
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        ordering = ['carrera__nombre', 'anio_cursado', 'cuatrimestre', 'nombre']
        unique_together = ['nombre', 'carrera']
        
    def __str__(self):
        return f"{self.nombre} - {self.carrera.nombre}"
    
    def get_absolute_url(self):
        return reverse('materias:detalle', kwargs={'pk': self.pk})
    
    def get_inscriptos_count(self):
        """Retorna la cantidad de alumnos inscriptos"""
        return self.inscripciones.filter(activa=True).count()
    
    def get_cupo_disponible(self):
        """Retorna el cupo disponible"""
        return self.cupo_maximo - self.get_inscriptos_count()
    
    def tiene_cupo_disponible(self):
        """Verifica si hay cupo disponible"""
        return self.get_cupo_disponible() > 0
    
    def puede_eliminarse(self):
        """Verifica si la materia puede eliminarse (no tiene inscripciones activas)"""
        return not self.inscripciones.filter(activa=True).exists()
    
    def get_cuatrimestre_display_short(self):
        """Retorna una versión corta del cuatrimestre"""
        if self.cuatrimestre == 0:
            return "Anual"
        return f"{self.cuatrimestre}° C"
    
    def get_estado_cupo(self):
        """Retorna el estado del cupo para mostrar en templates"""
        disponible = self.get_cupo_disponible()
        if disponible == 0:
            return {'clase': 'danger', 'texto': 'Sin cupo'}
        elif disponible <= 5:
            return {'clase': 'warning', 'texto': f'{disponible} disponibles'}
        else:
            return {'clase': 'success', 'texto': f'{disponible} disponibles'}
