from django.urls import path
from . import views

app_name = 'carreras'

urlpatterns = [
    # Vistas principales
    path('', views.CarreraListView.as_view(), name='lista'),
    path('crear/', views.CarreraCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.CarreraDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.CarreraUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.CarreraDeleteView.as_view(), name='eliminar'),
    
    # Vistas especiales
    path('por-modalidad/', views.CarrerasPorModalidadView.as_view(), name='por_modalidad'),
    
    # API endpoints
    path('api/activas/', views.carreras_activas_json, name='activas_json'),
]
