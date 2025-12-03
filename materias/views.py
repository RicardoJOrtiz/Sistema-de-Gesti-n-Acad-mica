from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, F, Q
from django.http import JsonResponse
from .models import Materia
from .forms import MateriaForm, FiltroMateriaForm
from carreras.models import Carrera
from usuarios.views import AdminRequiredMixin


class DocenteRequiredMixin(LoginRequiredMixin):
    """Mixin para vistas que requieren rol de docente"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol not in ['docente', 'administrador']:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class MateriaListView(ListView):
    """Vista para listar materias con filtros avanzados"""
    model = Materia
    template_name = 'materias/lista.html'
    context_object_name = 'materias'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Materia.objects.select_related('carrera').annotate(
            inscriptos=Count('inscripciones', filter=Q(inscripciones__activa=True))
        )
        
        # Aplicar filtros desde GET parameters
        carrera_id = self.request.GET.get('carrera')
        if carrera_id:
            queryset = queryset.filter(carrera_id=carrera_id)
        
        anio = self.request.GET.get('anio')
        if anio:
            queryset = queryset.filter(anio_cursado=anio)
        
        cuatrimestre = self.request.GET.get('cuatrimestre')
        if cuatrimestre:
            queryset = queryset.filter(cuatrimestre=cuatrimestre)
        
        con_cupo = self.request.GET.get('con_cupo')
        if con_cupo:
            queryset = queryset.filter(inscriptos__lt=F('cupo_maximo'))
        
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) | 
                Q(codigo__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )
        
        # Mostrar solo materias activas por defecto (excepto para administradores)
        if not self.request.user.is_authenticated or self.request.user.rol != 'administrador':
            queryset = queryset.filter(activa=True)
        
        return queryset.order_by('carrera__nombre', 'anio_cursado', 'cuatrimestre', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['carreras'] = Carrera.objects.filter(activa=True).order_by('nombre')
        context['filtro_form'] = FiltroMateriaForm(self.request.GET)
        
        # Estadísticas para el dashboard - usar queryset completo, no paginado
        queryset_completo = self.get_queryset()
        context['materias_activas'] = queryset_completo.filter(activa=True).count()
        context['materias_con_cupo'] = queryset_completo.filter(
            inscriptos__lt=F('cupo_maximo'), activa=True
        ).count()
        context['total_inscripciones'] = sum(
            materia.inscriptos for materia in queryset_completo if hasattr(materia, 'inscriptos')
        )
        
        return context


class MateriaDetailView(DetailView):
    """Vista de detalle de materia con inscripciones - Accesible para todos"""
    model = Materia
    template_name = 'materias/detalle.html'
    context_object_name = 'materia'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener inscripciones activas (para administradores y docentes de la materia)
        if self.request.user.is_authenticated:
            es_admin = self.request.user.rol == 'administrador'
            es_docente_materia = (self.request.user.rol == 'docente' and 
                                  self.object.docente == self.request.user)
            
            if es_admin or es_docente_materia:
                context['inscripciones'] = self.object.inscripciones.filter(
                    activa=True
                ).select_related('alumno').order_by('fecha_inscripcion')
                context['puede_ver_inscripciones'] = True
        
        # Verificar si el alumno puede inscribirse (está inscrito en la carrera y no en la materia)
        if self.request.user.is_authenticated and self.request.user.es_alumno():
            try:
                alumno = self.request.user.alumno_profile
                carreras_activas = alumno.get_carreras_activas()
                # Verificar que esté inscrito en la carrera
                en_carrera = self.object.carrera in carreras_activas
                # Verificar que NO esté ya inscrito en la materia (activamente)
                ya_inscrito = self.object.inscripciones.filter(
                    alumno=alumno, 
                    activa=True
                ).exists()
                context['puede_inscribirse'] = en_carrera and not ya_inscrito
                context['ya_inscrito'] = ya_inscrito
            except:
                context['puede_inscribirse'] = False
                context['ya_inscrito'] = False
        else:
            context['puede_inscribirse'] = False
            context['ya_inscrito'] = False
        
        return context


class MateriaCreateView(AdminRequiredMixin, CreateView):
    """Vista para crear materias"""
    model = Materia
    form_class = MateriaForm
    template_name = 'materias/form.html'
    success_url = reverse_lazy('materias:lista')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'✅ Materia "{self.object.nombre}" creada correctamente.'
        )
        return response


class MateriaUpdateView(AdminRequiredMixin, UpdateView):
    """Vista para editar materias"""
    model = Materia
    form_class = MateriaForm
    template_name = 'materias/form.html'
    
    def get_success_url(self):
        return reverse_lazy('materias:detalle', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'✅ Materia "{self.object.nombre}" actualizada correctamente.'
        )
        return response


class MateriaDeleteView(AdminRequiredMixin, DeleteView):
    """Vista para eliminar materias con validaciones de seguridad"""
    model = Materia
    template_name = 'materias/eliminar.html'
    success_url = reverse_lazy('materias:lista')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        materia = self.get_object()
        context['puede_eliminar'] = materia.puede_eliminarse()
        context['inscriptos_count'] = materia.get_inscriptos_count()
        return context
    
    def delete(self, request, *args, **kwargs):
        materia = self.get_object()
        nombre = materia.nombre
        
        # Validación de seguridad
        if not materia.puede_eliminarse():
            messages.error(
                request, 
                f'❌ No se puede eliminar la materia "{nombre}" porque tiene '
                f'{materia.get_inscriptos_count()} inscripciones activas.'
            )
            return redirect('materias:detalle', pk=materia.pk)
        
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request, 
            f'🗑️ Materia "{nombre}" eliminada correctamente.'
        )
        return response


class MateriasPorCarreraView(ListView):
    """Vista de materias filtradas por carrera"""
    model = Materia
    template_name = 'materias/por_carrera.html'
    context_object_name = 'materias'
    paginate_by = 20
    
    def get_queryset(self):
        self.carrera = get_object_or_404(Carrera, pk=self.kwargs['carrera_id'])
        return Materia.objects.filter(
            carrera=self.carrera, 
            activa=True
        ).annotate(
            inscriptos=Count('inscripciones', filter=Q(inscripciones__activa=True))
        ).order_by('anio_cursado', 'cuatrimestre', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['carrera'] = self.carrera
        
        # Calcular total de horas
        materias_list = context['materias']
        total_horas = sum(materia.carga_horaria for materia in materias_list)
        context['total_horas'] = total_horas
        
        # Verificar si el usuario es alumno y si está inscrito en esta carrera
        if self.request.user.is_authenticated and self.request.user.es_alumno():
            try:
                alumno = self.request.user.alumno_profile
                carreras_activas = alumno.get_carreras_activas()
                context['puede_inscribirse'] = self.carrera in carreras_activas
                context['alumno'] = alumno
            except:
                context['puede_inscribirse'] = False
        else:
            context['puede_inscribirse'] = False
        
        return context


class MateriasConCupoView(ListView):
    """Vista de materias con cupo disponible"""
    model = Materia
    template_name = 'materias/con_cupo.html'
    context_object_name = 'materias'
    paginate_by = 20
    
    def get_queryset(self):
        return Materia.objects.filter(activa=True).annotate(
            inscriptos=Count('inscripciones', filter=Q(inscripciones__activa=True))
        ).filter(inscriptos__lt=F('cupo_maximo')).select_related('carrera').order_by(
            'carrera__nombre', 'anio_cursado', 'cuatrimestre', 'nombre'
        )


# Vista AJAX para obtener materias por carrera (útil para formularios dinámicos)
def materias_por_carrera_ajax(request):
    """Vista AJAX para obtener materias de una carrera específica"""
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        carrera_id = request.GET.get('carrera_id')
        if carrera_id:
            materias = Materia.objects.filter(
                carrera_id=carrera_id, 
                activa=True
            ).values('id', 'nombre', 'codigo', 'anio_cursado', 'cuatrimestre')
            
            return JsonResponse({
                'materias': list(materias),
                'success': True
            })
    
    return JsonResponse({'success': False, 'error': 'Solicitud inválida'})


def verificar_cupo_ajax(request):
    """Vista AJAX para verificar el cupo disponible de una materia"""
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        materia_id = request.GET.get('materia_id')
        if materia_id:
            try:
                materia = Materia.objects.get(id=materia_id, activa=True)
                return JsonResponse({
                    'cupo_disponible': materia.get_cupo_disponible(),
                    'cupo_maximo': materia.cupo_maximo,
                    'inscriptos': materia.get_inscriptos_count(),
                    'tiene_cupo': materia.tiene_cupo_disponible(),
                    'success': True
                })
            except Materia.DoesNotExist:
                pass
    
    return JsonResponse({'success': False, 'error': 'Materia no encontrada'})


class MisMateriasDocenteView(DocenteRequiredMixin, ListView):
    """Vista para que el docente vea sus materias asignadas y listas de alumnos"""
    model = Materia
    template_name = 'materias/mis_materias_docente.html'
    context_object_name = 'materias'
    
    def get_queryset(self):
        # Solo las materias asignadas al docente actual
        return Materia.objects.filter(
            docente=self.request.user,
            activa=True
        ).select_related('carrera').prefetch_related(
            'inscripciones__alumno'
        ).order_by('carrera__nombre', 'anio_cursado', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar información de inscripciones por materia
        materias_con_alumnos = []
        total_alumnos = 0
        total_horas = 0
        
        for materia in context['materias']:
            inscripciones = materia.inscripciones.filter(activa=True).select_related('alumno')
            count_alumnos = inscripciones.count()
            materias_con_alumnos.append({
                'materia': materia,
                'inscripciones': inscripciones,
                'total_alumnos': count_alumnos
            })
            total_alumnos += count_alumnos
            total_horas += materia.carga_horaria
        
        context['materias_con_alumnos'] = materias_con_alumnos
        context['total_alumnos'] = total_alumnos
        context['total_horas'] = total_horas
        return context


class ListaAlumnosMateriaDocenteView(DocenteRequiredMixin, DetailView):
    """Vista detallada de alumnos de una materia específica para el docente"""
    model = Materia
    template_name = 'materias/lista_alumnos_materia.html'
    context_object_name = 'materia'
    
    def get_queryset(self):
        # Solo puede ver sus propias materias
        return Materia.objects.filter(docente=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todas las inscripciones activas de esta materia
        context['inscripciones'] = self.object.inscripciones.filter(
            activa=True
        ).select_related('alumno').order_by('alumno__apellido', 'alumno__nombre')
        return context
