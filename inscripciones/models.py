from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from alumnos.models import Alumno
from materias.models import Materia


class InscripcionManager(models.Manager):
    """
    Manager personalizado para Inscripciones
    Implementa abstracción de lógica de negocio
    """
    
    def inscripciones_activas(self):
        """Retorna solo las inscripciones activas"""
        return self.filter(activa=True)
    
    def por_carrera(self, carrera):
        """Filtra inscripciones por carrera"""
        return self.filter(materia__carrera=carrera)
    
    def por_alumno(self, alumno):
        """Filtra inscripciones por alumno"""
        return self.filter(alumno=alumno)
    
    def por_materia(self, materia):
        """Filtra inscripciones por materia"""
        return self.filter(materia=materia)
    
    def crear_inscripcion(self, alumno, materia):
        """
        Crea una inscripción validando las reglas de negocio
        Método de servicio que encapsula la lógica
        """
        # Validar si puede inscribirse
        puede, mensaje = alumno.puede_inscribirse_a(materia)
        if not puede:
            raise ValidationError(mensaje)
        
        # Crear la inscripción
        inscripcion = self.create(
            alumno=alumno,
            materia=materia,
            activa=True
        )
        
        return inscripcion


class Inscripcion(models.Model):
    """
    Modelo para las inscripciones de alumnos a materias
    Tabla intermedia con lógica de negocio
    """
    
    ESTADOS_CHOICES = [
        ('inscripto', 'Inscripto'),
        ('cursando', 'Cursando'),
        ('aprobado', 'Aprobado'),
        ('desaprobado', 'Desaprobado'),
        ('abandono', 'Abandono'),
        ('baja', 'Baja'),
    ]
    
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Alumno'
    )
    
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Materia'
    )
    
    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Inscripción'
    )
    
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS_CHOICES,
        default='inscripto',
        verbose_name='Estado'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Inscripción Activa'
    )
    
    nota_final = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Nota Final'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )
    
    fecha_baja = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Baja'
    )
    
    motivo_baja = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Motivo de Baja'
    )
    
    # Manager personalizado
    objects = InscripcionManager()
    
    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        unique_together = ['alumno', 'materia']
        ordering = ['-fecha_inscripcion']
        
    def __str__(self):
        return f"{self.alumno.get_full_name()} - {self.materia.nombre}"
    
    def get_absolute_url(self):
        return reverse('inscripciones:detalle', kwargs={'pk': self.pk})
    
    def clean(self):
        """
        Validaciones personalizadas del modelo
        Implementa validaciones de integridad
        """
        if self.alumno and self.materia:
            # Validar que la materia pertenezca a alguna carrera activa del alumno
            carreras_alumno = self.alumno.get_carreras_activas()
            if self.materia.carrera not in carreras_alumno:
                raise ValidationError(
                    'La materia debe pertenecer a una de las carreras activas del alumno'
                )
            
            # Validar cupo disponible (solo para inscripciones nuevas)
            if not self.pk and not self.materia.tiene_cupo_disponible():
                raise ValidationError(
                    'No hay cupo disponible en esta materia'
                )
    
    def save(self, *args, **kwargs):
        """
        Método save personalizado con validaciones
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    def dar_de_baja(self, motivo=''):
        """
        Da de baja la inscripción
        Método de instancia que encapsula la lógica
        """
        from django.utils import timezone
        
        self.activa = False
        self.estado = 'baja'
        self.fecha_baja = timezone.now()
        self.motivo_baja = motivo
        self.save()
    
    def reactivar(self):
        """
        Reactiva la inscripción si es posible
        """
        if not self.activa and self.materia.tiene_cupo_disponible():
            self.activa = True
            self.estado = 'inscripto'
            self.fecha_baja = None
            self.motivo_baja = ''
            self.save()
            return True
        return False
    
    def get_estado_display_color(self):
        """Retorna el color Bootstrap para el estado"""
        colors = {
            'inscripto': 'primary',
            'cursando': 'info',
            'aprobado': 'success',
            'desaprobado': 'danger',
            'abandono': 'warning',
            'baja': 'secondary',
        }
        return colors.get(self.estado, 'secondary')
    
    def puede_darse_de_baja(self):
        """Verifica si la inscripción puede darse de baja"""
        return self.activa and self.estado in ['inscripto', 'cursando']
