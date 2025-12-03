from django.contrib import admin
from .models import Alumno, InscripcionCarrera


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ['numero_legajo', 'nombre', 'apellido', 'dni', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'apellido', 'dni', 'numero_legajo']


@admin.register(InscripcionCarrera)
class InscripcionCarreraAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'carrera', 'fecha_inscripcion', 'activa']
    list_filter = ['activa', 'carrera']
    search_fields = ['alumno__nombre', 'alumno__apellido', 'carrera__nombre']
    date_hierarchy = 'fecha_inscripcion'
