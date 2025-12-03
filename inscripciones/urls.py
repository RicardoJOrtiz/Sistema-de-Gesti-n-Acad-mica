from django.urls import path
from . import views

app_name = 'inscripciones'

urlpatterns = [
    path('', views.InscripcionListView.as_view(), name='lista'),
    path('crear/', views.InscripcionCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.InscripcionDetailView.as_view(), name='detalle'),
    path('<int:pk>/dar-baja/', views.DarBajaInscripcionView.as_view(), name='dar_baja'),
    path('<int:pk>/reactivar/', views.ReactivarInscripcionView.as_view(), name='reactivar'),
    path('mis-inscripciones/', views.MisInscripcionesView.as_view(), name='mis_inscripciones'),
    path('seleccionar-carrera/', views.SeleccionarCarreraView.as_view(), name='seleccionar_carrera'),
    path('inscribirse/<int:materia_id>/', views.InscribirseView.as_view(), name='inscribirse'),
    path('desinscribirse/<int:materia_id>/', views.DesinscribirseView.as_view(), name='desinscribirse'),
    path('gestion-preceptor/', views.GestionInscripcionesPreceptorView.as_view(), name='gestion_preceptor'),
    
    # AJAX
    path('ajax/materias-por-alumno/', views.obtener_materias_por_alumno, name='ajax_materias_por_alumno'),
]
