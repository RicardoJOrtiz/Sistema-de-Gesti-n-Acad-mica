from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .models import Inscripcion
from .forms import InscripcionForm
from materias.models import Materia
from alumnos.models import Alumno
from usuarios.views import AdminRequiredMixin


class PreceptorRequiredMixin(LoginRequiredMixin):
    """Mixin para vistas que requieren rol de preceptor o administrador"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol not in ['preceptor', 'administrador']:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class InscripcionListView(PreceptorRequiredMixin, ListView):
    """Vista para listar inscripciones (acceso para preceptor y administrador)"""
    model = Inscripcion
    template_name = 'inscripciones/lista.html'
    context_object_name = 'inscripciones'
    paginate_by = 20
    
    def get_queryset(self):
        return Inscripcion.objects.select_related('alumno', 'materia', 'materia__carrera').order_by('-fecha_inscripcion')


class InscripcionDetailView(PreceptorRequiredMixin, DetailView):
    """Vista de detalle de inscripción (acceso para preceptor y administrador)"""
    model = Inscripcion
    template_name = 'inscripciones/detalle.html'
    context_object_name = 'inscripcion'


class InscripcionCreateView(PreceptorRequiredMixin, CreateView):
    """Vista para crear inscripciones (acceso para preceptor y administrador)"""
    model = Inscripcion
    template_name = 'inscripciones/crear.html'
    form_class = InscripcionForm
    success_url = reverse_lazy('inscripciones:lista')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(
                self.request, 
                f'Inscripción de {self.object.alumno.get_full_name()} '
                f'a {self.object.materia.nombre} creada correctamente.'
            )
            return response
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class MisInscripcionesView(LoginRequiredMixin, ListView):
    """Vista de inscripciones del alumno autenticado"""
    model = Inscripcion
    template_name = 'inscripciones/mis_inscripciones.html'
    context_object_name = 'inscripciones'
    
    def get_queryset(self):
        # Solo si es alumno
        if not self.request.user.es_alumno():
            return Inscripcion.objects.none()
        
        try:
            alumno = self.request.user.alumno_profile
            return Inscripcion.objects.filter(
                alumno=alumno
            ).select_related('materia', 'materia__carrera').order_by('-fecha_inscripcion')
        except:
            return Inscripcion.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar la carrera principal del alumno para el botón de inscripción
        if self.request.user.is_authenticated and self.request.user.es_alumno():
            try:
                alumno = self.request.user.alumno_profile
                context['carrera_principal'] = alumno.get_carrera_principal()
                # Contar inscripciones activas
                context['inscripciones_activas_count'] = self.get_queryset().filter(activa=True).count()
            except:
                context['carrera_principal'] = None
                context['inscripciones_activas_count'] = 0
        return context


class InscribirseView(LoginRequiredMixin, View):
    """Vista para que un alumno se inscriba a una materia"""
    
    def get(self, request, materia_id):
        if not request.user.es_alumno():
            messages.error(request, 'Solo los alumnos pueden inscribirse a materias.')
            return redirect('home')
        
        try:
            alumno = request.user.alumno_profile
            materia = get_object_or_404(Materia, pk=materia_id)
            
            # Verificar que la materia pertenece a una de sus carreras activas
            carreras_activas = alumno.get_carreras_activas()
            if materia.carrera not in carreras_activas:
                messages.error(request, f'No puedes inscribirte a materias de carreras en las que no estás inscripto.')
                return redirect('inscripciones:seleccionar_carrera')
            
            # Verificar si ya está inscripto
            if Inscripcion.objects.filter(alumno=alumno, materia=materia, activa=True).exists():
                messages.warning(request, f'Ya estás inscripto en {materia.nombre}')
                return redirect('inscripciones:mis_inscripciones')
            
            # Verificar cupo
            if not materia.tiene_cupo_disponible():
                messages.error(request, f'La materia {materia.nombre} no tiene cupo disponible')
                return redirect('materias:por_carrera', pk=materia.carrera.pk)
            
            context = {
                'materia': materia,
                'alumno': alumno,
            }
            return render(request, 'inscripciones/confirmar_inscripcion.html', context)
            
        except Exception as e:
            messages.error(request, str(e))
            return redirect('inscripciones:seleccionar_carrera')
    
    def post(self, request, materia_id):
        if not request.user.es_alumno():
            messages.error(request, 'Solo los alumnos pueden inscribirse a materias.')
            return redirect('home')
        
        try:
            alumno = request.user.alumno_profile
            materia = get_object_or_404(Materia, pk=materia_id)
            
            # Intentar inscribirse
            inscripcion = alumno.inscribirse_a(materia)
            messages.success(
                request, 
                f'Te has inscripto correctamente a {materia.nombre}'
            )
            
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('inscripciones:mis_inscripciones')


class SeleccionarCarreraView(LoginRequiredMixin, ListView):
    """Vista para que el alumno seleccione la carrera y vea sus materias"""
    template_name = 'inscripciones/seleccionar_carrera.html'
    context_object_name = 'carreras'
    
    def get_queryset(self):
        if not self.request.user.es_alumno():
            return []
        
        try:
            alumno = self.request.user.alumno_profile
            # Solo mostrar carreras activas del alumno
            return alumno.get_carreras_activas()
        except:
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.es_alumno():
            try:
                alumno = self.request.user.alumno_profile
                context['alumno'] = alumno
                # Obtener todas las carreras para información general
                from carreras.models import Carrera
                context['todas_carreras'] = Carrera.objects.filter(activa=True)
            except:
                pass
        return context


class DesinscribirseView(LoginRequiredMixin, View):
    """Vista para que un alumno se desinscriba de una materia"""
    
    def post(self, request, materia_id):
        if not request.user.es_alumno():
            messages.error(request, 'Solo los alumnos pueden desinscribirse de materias.')
            return redirect('home')
        
        try:
            alumno = request.user.alumno_profile
            materia = get_object_or_404(Materia, pk=materia_id)
            
            # Buscar inscripción activa
            inscripcion = Inscripcion.objects.filter(
                alumno=alumno, 
                materia=materia, 
                activa=True
            ).first()
            
            if not inscripcion:
                messages.warning(request, f'No estás inscripto en {materia.nombre}')
                return redirect('inscripciones:mis_inscripciones')
            
            # Dar de baja la inscripción
            inscripcion.dar_de_baja('Baja solicitada por el alumno')
            messages.success(
                request, 
                f'Te has desinscripto correctamente de {materia.nombre}'
            )
            
        except Exception as e:
            messages.error(request, f'Error al desinscribirse: {str(e)}')
        
        return redirect('inscripciones:mis_inscripciones')


class DarBajaInscripcionView(LoginRequiredMixin, View):
    """Vista para dar de baja una inscripción"""
    
    def post(self, request, pk):
        inscripcion = get_object_or_404(Inscripcion, pk=pk)
        
        # Verificar permisos
        if not (request.user.es_administrador() or 
                request.user.es_preceptor() or
                (request.user.es_alumno() and inscripcion.alumno.usuario == request.user)):
            messages.error(request, 'No tienes permisos para dar de baja esta inscripción.')
            return redirect('home')
        
        if inscripcion.puede_darse_de_baja():
            inscripcion.dar_de_baja('Baja solicitada por el usuario')
            messages.success(
                request, 
                f'Inscripción a {inscripcion.materia.nombre} dada de baja correctamente.'
            )
        else:
            messages.error(request, 'No se puede dar de baja esta inscripción.')
        
        # Redirigir según el tipo de usuario
        if request.user.es_administrador() or request.user.es_preceptor():
            return redirect('inscripciones:lista')
        else:
            return redirect('inscripciones:mis_inscripciones')


class ReactivarInscripcionView(LoginRequiredMixin, View):
    """Vista para reactivar (dar de alta) una inscripción dada de baja"""
    
    def post(self, request, pk):
        inscripcion = get_object_or_404(Inscripcion, pk=pk)
        
        # Verificar permisos - solo preceptor y administrador
        if not (request.user.es_administrador() or request.user.es_preceptor()):
            messages.error(request, 'No tienes permisos para reactivar esta inscripción.')
            return redirect('home')
        
        # Verificar que la inscripción está inactiva
        if inscripcion.activa:
            messages.warning(request, 'Esta inscripción ya está activa.')
            return redirect('inscripciones:lista')
        
        # Intentar reactivar
        if inscripcion.reactivar():
            messages.success(
                request,
                f'Inscripción de {inscripcion.alumno.get_full_name()} a {inscripcion.materia.nombre} reactivada correctamente.'
            )
        else:
            messages.error(
                request,
                f'No se puede reactivar la inscripción. Verifica que la materia tenga cupo disponible.'
            )
        
        return redirect('inscripciones:lista')


class GestionInscripcionesPreceptorView(PreceptorRequiredMixin, ListView):
    """Vista para que el preceptor gestione inscripciones (solo visual)"""
    model = Inscripcion
    template_name = 'inscripciones/gestion_preceptor.html'
    context_object_name = 'inscripciones'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Inscripcion.objects.select_related(
            'alumno', 'materia', 'materia__carrera'
        ).order_by('-fecha_inscripcion')
        
        # Filtros opcionales
        carrera_id = self.request.GET.get('carrera')
        materia_id = self.request.GET.get('materia')
        estado = self.request.GET.get('estado')
        
        if carrera_id:
            queryset = queryset.filter(materia__carrera_id=carrera_id)
        if materia_id:
            queryset = queryset.filter(materia_id=materia_id)
        if estado:
            queryset = queryset.filter(activa=(estado == 'activa'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from carreras.models import Carrera
        context['carreras'] = Carrera.objects.all()
        context['materias'] = Materia.objects.all()
        return context


def obtener_materias_por_alumno(request):
    """Vista AJAX para obtener las materias de la carrera del alumno"""
    alumno_id = request.GET.get('alumno_id')
    
    if not alumno_id:
        return JsonResponse({'materias': []})
    
    try:
        alumno = Alumno.objects.get(pk=alumno_id)
        carrera = alumno.get_carrera_principal()
        
        if not carrera:
            return JsonResponse({'materias': []})
        
        # Obtener materias activas de la carrera del alumno
        materias = Materia.objects.filter(
            carrera=carrera,
            activa=True
        ).values('id', 'nombre', 'codigo', 'anio_cursado', 'cuatrimestre').order_by('anio_cursado', 'nombre')
        
        return JsonResponse({
            'materias': list(materias),
            'carrera': carrera.nombre
        })
    except Alumno.DoesNotExist:
        return JsonResponse({'materias': [], 'error': 'Alumno no encontrado'})
