from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticación
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('cambiar-password/', views.CambiarPasswordView.as_view(), name='cambiar_password'),
    
    # Recuperación de contraseña
    path('recuperar-password/', views.RecuperarPasswordView.as_view(), name='recuperar_password'),
    path('recuperar-password/enviado/', views.RecuperarPasswordEnviadoView.as_view(), name='recuperar_password_enviado'),
    path('restablecer-password/<uidb64>/<token>/', views.RestablecerPasswordView.as_view(), name='restablecer_password'),
    path('password-restablecido/', views.PasswordRestablecidoView.as_view(), name='password_restablecido'),
    
    # Gestión de usuarios (solo administradores)
    path('', views.UsuarioListView.as_view(), name='lista'),
    path('docentes/', views.DocenteListView.as_view(), name='lista_docentes'),
    path('preceptores/', views.PreceptorListView.as_view(), name='lista_preceptores'),
    path('invitados/', views.InvitadoListView.as_view(), name='lista_invitados'),
    path('crear/', views.UsuarioCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.UsuarioDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='eliminar'),
    
    # Perfil de usuario
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('perfil/editar/', views.EditarPerfilView.as_view(), name='editar_perfil'),
]
