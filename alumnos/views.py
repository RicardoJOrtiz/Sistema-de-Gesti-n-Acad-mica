from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Alumno
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


class AlumnoListView(PreceptorRequiredMixin, ListView):
    """Vista para listar alumnos (acceso para preceptor y administrador)"""
    model = Alumno
    template_name = 'alumnos/lista.html'
    context_object_name = 'alumnos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Alumno.objects.filter(activo=True).select_related('usuario').prefetch_related('carreras')
        
        # Búsqueda
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) |
                Q(apellido__icontains=buscar) |
                Q(dni__icontains=buscar) |
                Q(numero_legajo__icontains=buscar)
            )
        
        # Filtro por carrera
        carrera_id = self.request.GET.get('carrera')
        if carrera_id:
            queryset = queryset.filter(carreras__id=carrera_id, inscripcioncarrera__activa=True).distinct()
        
        # Filtro por año de ingreso
        anio = self.request.GET.get('anio')
        if anio:
            queryset = queryset.filter(fecha_ingreso__year=anio)
        
        return queryset.order_by('apellido', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from carreras.models import Carrera
        from django.db.models import Min
        
        context['carreras'] = Carrera.objects.filter(activa=True).order_by('nombre')
        # Obtener los años de ingreso disponibles
        anios = Alumno.objects.filter(activo=True).values_list('fecha_ingreso__year', flat=True).distinct().order_by('-fecha_ingreso__year')
        context['anios_disponibles'] = sorted(set(anios), reverse=True)
        context['buscar'] = self.request.GET.get('buscar', '')
        context['carrera_filtro'] = self.request.GET.get('carrera', '')
        context['anio_filtro'] = self.request.GET.get('anio', '')
        return context


class AlumnoDetailView(PreceptorRequiredMixin, DetailView):
    """Vista de detalle de alumno (acceso para preceptor y administrador)"""
    model = Alumno
    template_name = 'alumnos/detalle.html'
    context_object_name = 'alumno'


class AlumnoCreateView(AdminRequiredMixin, CreateView):
    """Vista para crear alumnos"""
    model = Alumno
    template_name = 'alumnos/crear.html'
    fields = ['usuario', 'carrera', 'numero_legajo', 'nombre', 'apellido', 'dni', 'email', 'telefono', 'fecha_nacimiento', 'direccion', 'fecha_ingreso']
    success_url = reverse_lazy('alumnos:lista')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Alumno {self.object.get_full_name()} creado correctamente.')
        return response


class AlumnoUpdateView(AdminRequiredMixin, UpdateView):
    """Vista para editar alumnos"""
    model = Alumno
    template_name = 'alumnos/editar.html'
    fields = ['carrera', 'numero_legajo', 'nombre', 'apellido', 'email', 'telefono', 'fecha_nacimiento', 'direccion', 'fecha_ingreso', 'activo']
    
    def get_success_url(self):
        return reverse_lazy('alumnos:detalle', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Alumno {self.object.get_full_name()} actualizado correctamente.')
        return response


class AlumnoDeleteView(AdminRequiredMixin, DeleteView):
    """Vista para eliminar alumnos"""
    model = Alumno
    template_name = 'alumnos/eliminar.html'
    success_url = reverse_lazy('alumnos:lista')
    
    def delete(self, request, *args, **kwargs):
        alumno = self.get_object()
        nombre = alumno.get_full_name()
        
        if not alumno.puede_eliminarse():
            messages.error(request, 'No se puede eliminar el alumno porque tiene inscripciones.')
            return redirect('alumnos:lista')
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Alumno {nombre} eliminado correctamente.')
        return response
