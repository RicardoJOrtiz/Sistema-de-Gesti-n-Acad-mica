from django.urls import path
from . import views

app_name = 'alumnos'

urlpatterns = [
    path('', views.AlumnoListView.as_view(), name='lista'),
    path('crear/', views.AlumnoCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.AlumnoDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.AlumnoUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.AlumnoDeleteView.as_view(), name='eliminar'),
]
