"""
Middleware para gestión de sesiones y auto-logout
"""
from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from datetime import timedelta


class SessionTimeoutMiddleware:
    """
    Middleware que gestiona el timeout de sesión
    Agrega información al contexto sobre el tiempo restante
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Obtener el tiempo de última actividad
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Calcular tiempo transcurrido
                elapsed_time = (timezone.now() - timezone.datetime.fromisoformat(last_activity)).total_seconds()
                timeout = settings.SESSION_COOKIE_AGE
                tiempo_restante = int(timeout - elapsed_time)
                
                # Agregar información de sesión al request
                request.session_timeout = tiempo_restante
                request.session_warning = tiempo_restante <= 300  # Advertir en últimos 5 minutos
            else:
                request.session_timeout = settings.SESSION_COOKIE_AGE
                request.session_warning = False
            
            # Actualizar última actividad
            request.session['last_activity'] = timezone.now().isoformat()
            # Resetear warning cuando hay actividad
            if 'warning_shown' in request.session:
                del request.session['warning_shown']
        
        response = self.get_response(request)
        return response


class ForcePasswordChangeMiddleware:
    """
    Middleware que obliga a los usuarios a cambiar su contraseña
    si tienen el flag debe_cambiar_password activado
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs que no requieren cambio de contraseña
        exempt_urls = [
            reverse('usuarios:cambiar_password'),
            reverse('usuarios:logout'),
        ]
        
        # Verificar si el usuario debe cambiar contraseña
        if request.user.is_authenticated and request.user.debe_cambiar_password:
            # Permitir acceso solo a las URLs exentas
            if request.path not in exempt_urls and not request.path.startswith('/static/'):
                return redirect('usuarios:cambiar_password')
        
        response = self.get_response(request)
        return response
