from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse
from usuarios.models import Usuario
from carreras.models import Carrera


class Persona(models.Model):
    """
    Clase base abstracta para personas en el sistema
    Implementa herencia según los principios de POO
    """
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    
    apellido = models.CharField(
        max_length=100,
        verbose_name='Apellido'
    )
    
    dni = models.CharField(
        max_length=8,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\d{7,8}$',
            message='El DNI debe tener 7 u 8 dígitos numéricos.'
        )],
        verbose_name='DNI'
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
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
    
    fecha_nacimiento = models.DateField(
        verbose_name='Fecha de Nacimiento'
    )
    
    direccion = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )
    
    class Meta:
        abstract = True
        
    def get_full_name(self):
        """Retorna el nombre completo"""
        return f"{self.nombre} {self.apellido}"
    
    def get_edad(self):
        """Calcula y retorna la edad"""
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )


class Alumno(Persona):
    """
    Modelo para alumnos que hereda de Persona
    Implementa herencia según los principios de POO
    """
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='alumno_profile',
        null=True,
        blank=True,
        verbose_name='Usuario del Sistema'
    )
    
    # Relación muchos a muchos con Carreras a través de InscripcionCarrera
    carreras = models.ManyToManyField(
        Carrera,
        through='InscripcionCarrera',
        related_name='alumnos_inscritos',
        verbose_name='Carreras'
    )
    
    numero_legajo = models.CharField(
        max_length=15,
        unique=True,
        verbose_name='Número de Legajo'
    )
    
    fecha_ingreso = models.DateField(
        verbose_name='Fecha de Ingreso'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones'
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
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'
        ordering = ['apellido', 'nombre']
        
    def __str__(self):
        return f"{self.get_full_name()} - {self.numero_legajo}"
    
    def get_absolute_url(self):
        return reverse('alumnos:detalle', kwargs={'pk': self.pk})
    
    def get_materias_inscriptas(self):
        """Retorna las materias en las que está inscripto"""
        return self.inscripciones.filter(activa=True)
    
    def get_materias_count(self):
        """Retorna la cantidad de materias inscriptas"""
        return self.get_materias_inscriptas().count()
    
    def get_anio_cursado_actual(self, carrera=None):
        """
        Calcula en qué año está el alumno según su fecha de ingreso
        Si se especifica carrera, usa la fecha de inscripción a esa carrera
        """
        from datetime import date
        
        if carrera:
            # Buscar fecha de inscripción específica a la carrera
            inscripcion = self.inscripcioncarrera.filter(carrera=carrera, activa=True).first()
            if inscripcion:
                fecha_ref = inscripcion.fecha_inscripcion
            else:
                return 1  # Si no está inscripto, retorna 1
        else:
            fecha_ref = self.fecha_ingreso
        
        # Calcular años desde ingreso
        today = date.today()
        anios_cursados = today.year - fecha_ref.year
        
        # Si aún no llegó al mes de ingreso, resta un año
        if (today.month, today.day) < (fecha_ref.month, fecha_ref.day):
            anios_cursados -= 1
        
        # El año de cursado es al menos 1
        return max(1, anios_cursados + 1)
    
    def puede_inscribirse_a(self, materia):
        """
        Verifica si el alumno puede inscribirse a una materia
        Aplica validaciones de negocio
        """
        # Verificar si el alumno está activo
        if not self.activo:
            return False, "El alumno no está activo"
        
        # Verificar si la materia pertenece a alguna de sus carreras activas
        carreras_activas = self.get_carreras_activas()
        if materia.carrera not in carreras_activas:
            return False, "La materia no pertenece a ninguna de tus carreras activas"
        
        # Verificar si ya está inscripto
        if self.inscripciones.filter(materia=materia, activa=True).exists():
            return False, "Ya está inscripto en esta materia"
        
        # Verificar año de cursado - el alumno solo puede inscribirse a materias de su año actual o anteriores
        anio_alumno = self.get_anio_cursado_actual(materia.carrera)
        if materia.anio_cursado > anio_alumno:
            return False, f"No puede inscribirse a materias de {materia.anio_cursado}° año. Actualmente está en {anio_alumno}° año"
        
        # Verificar cupo disponible
        if not materia.tiene_cupo_disponible():
            return False, "No hay cupo disponible"
        
        return True, "Puede inscribirse"
    
    def inscribirse_a(self, materia):
        """
        Inscribe al alumno a una materia
        Retorna la inscripción creada o reactivada
        """
        from inscripciones.models import Inscripcion
        
        # Verificar si existe una inscripción previa (activa o inactiva)
        inscripcion_existente = self.inscripciones.filter(materia=materia).first()
        
        if inscripcion_existente:
            # Si existe y está inactiva, reactivarla
            if not inscripcion_existente.activa:
                if materia.tiene_cupo_disponible():
                    inscripcion_existente.reactivar()
                    return inscripcion_existente
                else:
                    raise ValueError("No hay cupo disponible")
            else:
                raise ValueError("Ya está inscripto en esta materia")
        
        # Si no existe, verificar si puede inscribirse
        puede, mensaje = self.puede_inscribirse_a(materia)
        if not puede:
            raise ValueError(mensaje)
        
        # Crear la inscripción
        inscripcion = Inscripcion.objects.create(
            alumno=self,
            materia=materia,
            estado='inscripto',
            activa=True
        )
        
        return inscripcion
    
    def get_materias_disponibles(self):
        """Retorna las materias de sus carreras en las que NO está inscripto"""
        from materias.models import Materia
        materias_inscriptas = self.inscripciones.filter(activa=True).values_list('materia_id', flat=True)
        carreras_activas = self.inscripcioncarrera.filter(activa=True).values_list('carrera_id', flat=True)
        return Materia.objects.filter(
            carrera_id__in=carreras_activas,
            activa=True
        ).exclude(id__in=materias_inscriptas)
    
    def get_carrera_principal(self):
        """Retorna la carrera principal (la primera activa o la más antigua)"""
        inscripcion_principal = self.inscripcioncarrera.filter(activa=True).order_by('fecha_inscripcion').first()
        return inscripcion_principal.carrera if inscripcion_principal else None
    
    def get_carreras_activas(self):
        """Retorna todas las carreras activas del alumno"""
        return self.carreras.filter(
            inscripcioncarrera__activa=True
        ).distinct()
    
    def puede_eliminarse(self):
        """Verifica si el alumno puede eliminarse (no tiene inscripciones activas)"""
        return not self.inscripciones.filter(activa=True).exists()


class InscripcionCarrera(models.Model):
    """
    Modelo intermedio para la relación Alumno-Carrera
    Permite que un alumno esté inscripto en múltiples carreras
    """
    
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name='inscripcioncarrera',
        verbose_name='Alumno'
    )
    
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.CASCADE,
        verbose_name='Carrera'
    )
    
    fecha_inscripcion = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de Inscripción'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Inscripción Activa'
    )
    
    fecha_baja = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Baja'
    )
    
    motivo_baja = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Motivo de Baja'
    )
    
    class Meta:
        verbose_name = 'Inscripción a Carrera'
        verbose_name_plural = 'Inscripciones a Carreras'
        unique_together = ['alumno', 'carrera']
        ordering = ['-fecha_inscripcion']
    
    def __str__(self):
        return f"{self.alumno.get_full_name()} - {self.carrera.nombre}"
    
    def dar_de_baja(self, motivo=''):
        """Da de baja la inscripción a la carrera"""
        from django.utils import timezone
        self.activa = False
        self.fecha_baja = timezone.now().date()
        self.motivo_baja = motivo
        self.save()
