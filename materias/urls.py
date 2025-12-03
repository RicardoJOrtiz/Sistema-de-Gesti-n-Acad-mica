from django.urls import path
from . import views

app_name = 'materias'

urlpatterns = [
    # Vistas principales
    path('', views.MateriaListView.as_view(), name='lista'),
    path('crear/', views.MateriaCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.MateriaDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.MateriaUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.MateriaDeleteView.as_view(), name='eliminar'),
    
    # Vistas de filtrado y búsqueda
    path('por-carrera/<int:carrera_id>/', views.MateriasPorCarreraView.as_view(), name='por_carrera'),
    path('con-cupo/', views.MateriasConCupoView.as_view(), name='con_cupo'),
    
    # Vistas para docentes
    path('mis-materias/', views.MisMateriasDocenteView.as_view(), name='mis_materias_docente'),
    path('mis-materias/<int:pk>/alumnos/', views.ListaAlumnosMateriaDocenteView.as_view(), name='lista_alumnos'),
    
    # Vistas AJAX
    path('ajax/por-carrera/', views.materias_por_carrera_ajax, name='ajax_por_carrera'),
    path('ajax/verificar-cupo/', views.verificar_cupo_ajax, name='ajax_verificar_cupo'),
]
