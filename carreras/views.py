from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from .models import Carrera
from .forms import CarreraForm, FiltroCarreraForm
from usuarios.views import AdminRequiredMixin


class CarreraListView(ListView):
    """Vista para listar carreras con filtros avanzados"""
    model = Carrera
    template_name = 'carreras/lista.html'
    context_object_name = 'carreras'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Carrera.objects.annotate(
            total_materias=Count('materias', filter=Q(materias__activa=True)),
            total_alumnos=Count('alumnos', filter=Q(alumnos__activo=True))
        )
        
        # Aplicar filtros desde GET parameters
        modalidad = self.request.GET.get('modalidad')
        if modalidad:
            queryset = queryset.filter(modalidad=modalidad)
        
        duracion = self.request.GET.get('duracion')
        if duracion:
            queryset = queryset.filter(duracion_anios=duracion)
        
        activa = self.request.GET.get('activa')
        if activa == 'True':
            queryset = queryset.filter(activa=True)
        elif activa == 'False':
            queryset = queryset.filter(activa=False)
        
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) | 
                Q(codigo__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )
        
        # Mostrar solo carreras activas por defecto (excepto para administradores)
        if self.request.user.rol != 'administrador':
            queryset = queryset.filter(activa=True)
        
        return queryset.order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro_form'] = FiltroCarreraForm(self.request.GET)
        
        # Estadísticas para el dashboard
        carreras = context['carreras']
        context['carreras_activas'] = carreras.filter(activa=True).count()
        context['total_materias'] = sum(
            carrera.total_materias for carrera in carreras if hasattr(carrera, 'total_materias')
        )
        context['total_alumnos'] = sum(
            carrera.total_alumnos for carrera in carreras if hasattr(carrera, 'total_alumnos')
        )
        
        return context


class CarreraDetailView(LoginRequiredMixin, DetailView):
    """Vista de detalle de carrera con materias y estadísticas"""
    model = Carrera
    template_name = 'carreras/detalle.html'
    context_object_name = 'carrera'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrera = self.get_object()
        
        # Obtener materias de la carrera agrupadas por año
        context['materias_por_anio'] = {}
        materias = carrera.materias.filter(activa=True).order_by('anio_cursado', 'cuatrimestre', 'nombre')
        
        for materia in materias:
            anio = materia.anio_cursado
            if anio not in context['materias_por_anio']:
                context['materias_por_anio'][anio] = []
            context['materias_por_anio'][anio].append(materia)
        
        # Estadísticas
        context['total_materias'] = materias.count()
        context['total_alumnos'] = carrera.get_alumnos_count()
        
        return context


class CarreraCreateView(AdminRequiredMixin, CreateView):
    """Vista para crear nueva carrera"""
    model = Carrera
    form_class = CarreraForm
    template_name = 'carreras/form.html'
    success_url = reverse_lazy('carreras:lista')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Carrera "{self.object.nombre}" creada exitosamente.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Carrera'
        context['accion'] = 'Crear'
        return context


class CarreraUpdateView(AdminRequiredMixin, UpdateView):
    """Vista para actualizar carrera"""
    model = Carrera
    form_class = CarreraForm
    template_name = 'carreras/form.html'
    success_url = reverse_lazy('carreras:lista')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Carrera "{self.object.nombre}" actualizada exitosamente.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Carrera: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context


class CarreraDeleteView(AdminRequiredMixin, DeleteView):
    """Vista para eliminar carrera con validaciones"""
    model = Carrera
    template_name = 'carreras/eliminar.html'
    success_url = reverse_lazy('carreras:lista')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verificar si tiene alumnos activos
        if self.object.alumnos.filter(activo=True).exists():
            messages.error(request, 
                f'No se puede eliminar la carrera "{self.object.nombre}" porque tiene alumnos activos.')
            return redirect('carreras:detalle', pk=self.object.pk)
        
        # Verificar si tiene materias activas
        if self.object.materias.filter(activa=True).exists():
            messages.warning(request, 
                f'La carrera "{self.object.nombre}" tiene materias activas. Éstas serán desactivadas.')
            # Desactivar las materias en lugar de eliminarlas
            self.object.materias.update(activa=False)
        
        messages.success(request, f'Carrera "{self.object.nombre}" eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrera = self.get_object()
        
        # Información para mostrar en la confirmación
        context['alumnos_count'] = carrera.alumnos.filter(activo=True).count()
        context['materias_count'] = carrera.materias.filter(activa=True).count()
        context['puede_eliminar'] = context['alumnos_count'] == 0
        
        return context


# Vistas auxiliares
def carreras_activas_json(request):
    """Vista para obtener carreras activas en formato JSON (para AJAX)"""
    from django.http import JsonResponse
    
    if request.method == 'GET':
        carreras = Carrera.objects.filter(activa=True).values('id', 'nombre', 'codigo')
        return JsonResponse(list(carreras), safe=False)


class CarrerasPorModalidadView(ListView):
    """Vista para mostrar carreras agrupadas por modalidad"""
    model = Carrera
    template_name = 'carreras/por_modalidad.html'
    context_object_name = 'carreras'
    
    def get_queryset(self):
        return Carrera.objects.filter(activa=True).order_by('modalidad', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agrupar carreras por modalidad
        carreras_por_modalidad = {}
        for carrera in context['carreras']:
            modalidad = carrera.get_modalidad_display()
            if modalidad not in carreras_por_modalidad:
                carreras_por_modalidad[modalidad] = []
            carreras_por_modalidad[modalidad].append(carrera)
        
        context['carreras_por_modalidad'] = carreras_por_modalidad
        return context


class CarreraCreateView(AdminRequiredMixin, CreateView):
    """Vista para crear carreras"""
    model = Carrera
    template_name = 'carreras/crear.html'
    fields = ['nombre', 'codigo', 'descripcion', 'duracion_anios', 'titulo_otorgado', 'modalidad']
    success_url = reverse_lazy('carreras:lista')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Carrera {self.object.nombre} creada correctamente.')
        return response


class CarreraUpdateView(AdminRequiredMixin, UpdateView):
    """Vista para editar carreras"""
    model = Carrera
    template_name = 'carreras/editar.html'
    fields = ['nombre', 'codigo', 'descripcion', 'duracion_anios', 'titulo_otorgado', 'modalidad', 'activa']
    
    def get_success_url(self):
        return reverse_lazy('carreras:detalle', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Carrera {self.object.nombre} actualizada correctamente.')
        return response


class CarreraDeleteView(AdminRequiredMixin, DeleteView):
    """Vista para eliminar carreras"""
    model = Carrera
    template_name = 'carreras/eliminar.html'
    success_url = reverse_lazy('carreras:lista')
    
    def delete(self, request, *args, **kwargs):
        carrera = self.get_object()
        nombre = carrera.nombre
        
        if not carrera.puede_eliminarse():
            messages.error(request, 'No se puede eliminar la carrera porque tiene materias o alumnos asociados.')
            return redirect('carreras:lista')
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Carrera {nombre} eliminada correctamente.')
        return response


class OfertaAcademicaView(ListView):
    """Vista de oferta académica para alumnos"""
    model = Carrera
    template_name = 'carreras/oferta.html'
    context_object_name = 'carreras'
    
    def get_queryset(self):
        return Carrera.objects.filter(activa=True).prefetch_related('materias').order_by('nombre')
