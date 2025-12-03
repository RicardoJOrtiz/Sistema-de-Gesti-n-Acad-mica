from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login, update_session_auth_hash
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from datetime import date, datetime, timedelta
import secrets
import string

from .models import Usuario, PerfilUsuario
from .forms import CustomLoginForm, UsuarioCreateForm, UsuarioUpdateForm, CustomPasswordChangeForm, PerfilUsuarioForm
from .perfil_forms import PerfilUpdateForm


class CustomLoginView(LoginView):
    """
    Vista personalizada de inicio de sesión
    """
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Maneja el login exitoso"""
        response = super().form_valid(form)
        user = form.get_user()
        
        # Verificar si debe cambiar contraseña
        if user.debe_cambiar_password:
            messages.warning(
                self.request, 
                'Debes cambiar tu contraseña antes de continuar.'
            )
            return redirect('usuarios:cambiar_password')
        
        messages.success(self.request, f'Bienvenido, {user.get_full_name()}!')
        return response


class CustomLogoutView(LogoutView):
    """
    Vista personalizada de cierre de sesión
    """
    template_name = 'usuarios/logout.html'
    http_method_names = ['get', 'post']  # Permitir GET y POST
    
    def get(self, request, *args, **kwargs):
        """Maneja logout por GET request"""
        if request.user.is_authenticated:
            messages.success(request, 'Has cerrado sesión correctamente.')
        return super().post(request, *args, **kwargs)  # Usar la lógica de POST
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CambiarPasswordView(LoginRequiredMixin, PasswordChangeView):
    """
    Vista para cambiar contraseña
    """
    form_class = CustomPasswordChangeForm
    template_name = 'usuarios/cambiar_password.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        """Marca que ya no debe cambiar contraseña"""
        response = super().form_valid(form)
        
        # Actualizar el flag de cambio de contraseña
        self.request.user.debe_cambiar_password = False
        self.request.user.save()
        
        messages.success(
            self.request, 
            'Tu contraseña ha sido actualizada correctamente.'
        )
        return response


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin que requiere que el usuario sea administrador
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_administrador()
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')


class UsuarioListView(AdminRequiredMixin, ListView):
    """
    Vista para listar usuarios (solo administradores)
    """
    model = Usuario
    template_name = 'usuarios/lista.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Usuario.objects.all()
        
        # Filtro por rol
        rol = self.request.GET.get('rol')
        if rol:
            queryset = queryset.filter(rol=rol)
        
        # Búsqueda por nombre, DNI o email
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar) |
                Q(dni__icontains=buscar) |
                Q(email__icontains=buscar)
            )
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = Usuario.ROLES_CHOICES
        context['filtro_rol'] = self.request.GET.get('rol', '')
        context['buscar'] = self.request.GET.get('buscar', '')
        return context


class PreceptorRequiredMixin(LoginRequiredMixin):
    """Mixin para vistas que requieren rol de preceptor o administrador"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol not in ['preceptor', 'administrador']:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class DocenteListView(PreceptorRequiredMixin, ListView):
    """
    Vista para listar docentes (acceso para preceptor y administrador)
    """
    model = Usuario
    template_name = 'usuarios/lista_docentes.html'
    context_object_name = 'docentes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Usuario.objects.filter(rol='docente')
        
        # Búsqueda por nombre, DNI o email
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar) |
                Q(dni__icontains=buscar) |
                Q(email__icontains=buscar)
            )
        
        return queryset.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buscar'] = self.request.GET.get('buscar', '')
        return context


class PreceptorListView(AdminRequiredMixin, ListView):
    """
    Vista para listar preceptores (acceso solo para administrador)
    """
    model = Usuario
    template_name = 'usuarios/lista_preceptores.html'
    context_object_name = 'preceptores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Usuario.objects.filter(rol='preceptor')
        
        # Búsqueda por nombre, DNI o email
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar) |
                Q(dni__icontains=buscar) |
                Q(email__icontains=buscar)
            )
        
        return queryset.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buscar'] = self.request.GET.get('buscar', '')
        return context


class InvitadoListView(AdminRequiredMixin, ListView):
    """
    Vista para listar visitantes/invitados (acceso solo para administrador)
    """
    model = Usuario
    template_name = 'usuarios/lista_invitados.html'
    context_object_name = 'invitados'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Usuario.objects.filter(rol='invitado')
        
        # Búsqueda por nombre, DNI o email
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar) |
                Q(dni__icontains=buscar) |
                Q(email__icontains=buscar)
            )
        
        return queryset.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buscar'] = self.request.GET.get('buscar', '')
        return context


class UsuarioDetailView(AdminRequiredMixin, DetailView):
    """
    Vista de detalle de usuario
    """
    model = Usuario
    template_name = 'usuarios/detalle.html'
    context_object_name = 'usuario'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.get_object()
        
        # Calcular edad si tiene fecha de nacimiento
        if usuario.fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            edad = hoy.year - usuario.fecha_nacimiento.year
            # Ajustar si aún no cumplió años este año
            if (hoy.month, hoy.day) < (usuario.fecha_nacimiento.month, usuario.fecha_nacimiento.day):
                edad -= 1
            context['edad'] = edad
        
        return context


class UsuarioCreateView(AdminRequiredMixin, CreateView):
    """
    Vista para crear usuarios
    """
    model = Usuario
    form_class = UsuarioCreateForm
    template_name = 'usuarios/crear.html'
    success_url = reverse_lazy('usuarios:lista')
    
    def form_valid(self, form):
        """Genera contraseña inicial y crea el usuario"""
        with transaction.atomic():
            # Generar contraseña inicial (DNI del usuario)
            dni = form.cleaned_data['dni']
            materias_asignadas = form.cleaned_data.get('materias', [])
            
            form.instance.set_password(dni)
            form.instance.debe_cambiar_password = True
            
            response = super().form_valid(form)
            
            # Crear perfil de usuario
            PerfilUsuario.objects.create(usuario=self.object)
            
            # Si el usuario es docente, asignar materias
            if self.object.rol == 'docente' and materias_asignadas:
                for materia in materias_asignadas:
                    materia.docente = self.object
                    materia.save()
                
                messages.info(
                    self.request,
                    f'Se asignaron {materias_asignadas.count()} materia(s) al docente'
                )
            
            # Si el usuario es alumno, crear automáticamente el registro de Alumno
            if self.object.rol == 'alumno':
                from alumnos.models import Alumno, InscripcionCarrera
                
                # Obtener la carrera seleccionada en el formulario
                carrera = form.cleaned_data.get('carrera')
                
                if carrera:
                    # Crear el alumno
                    alumno = Alumno.objects.create(
                        usuario=self.object,
                        numero_legajo=dni,  # Usar DNI como legajo
                        nombre=self.object.first_name,
                        apellido=self.object.last_name,
                        dni=dni,
                        email=self.object.email,
                        telefono=form.cleaned_data.get('telefono', ''),
                        fecha_nacimiento=form.cleaned_data.get('fecha_nacimiento'),
                        direccion=form.cleaned_data.get('direccion', ''),
                        fecha_ingreso=date.today(),
                        activo=True
                    )
                    
                    # Crear la inscripción a la carrera
                    InscripcionCarrera.objects.create(
                        alumno=alumno,
                        carrera=carrera,
                        activa=True
                    )
                    
                    messages.info(
                        self.request,
                        f'Se creó el registro de alumno en la carrera {carrera.nombre} con legajo: {dni}'
                    )
            
            messages.success(
                self.request, 
                f'Usuario {self.object.get_full_name()} creado correctamente. '
                f'Contraseña inicial: {dni}'
            )
            
            return response


class UsuarioUpdateView(AdminRequiredMixin, UpdateView):
    """
    Vista para editar usuarios
    """
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'usuarios/editar.html'
    
    def get_success_url(self):
        return reverse_lazy('usuarios:detalle', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Verificar si el usuario está intentando desactivarse a sí mismo
        if form.instance == self.request.user and not form.cleaned_data.get('is_active'):
            messages.error(
                self.request,
                'No puedes desactivar tu propia cuenta. Solicita a otro administrador que lo haga.'
            )
            return self.form_invalid(form)
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Si el usuario es docente, actualizar materias asignadas
            if self.object.rol == 'docente':
                from materias.models import Materia
                
                materias_seleccionadas = form.cleaned_data.get('materias', [])
                
                # Desasignar materias que ya no están seleccionadas
                Materia.objects.filter(docente=self.object).update(docente=None)
                
                # Asignar las nuevas materias seleccionadas
                if materias_seleccionadas:
                    for materia in materias_seleccionadas:
                        materia.docente = self.object
                        materia.save()
                    
                    messages.info(
                        self.request,
                        f'Se asignaron {len(materias_seleccionadas)} materia(s) al docente'
                    )
            
            messages.success(
                self.request, 
                f'Usuario {self.object.get_full_name()} actualizado correctamente.'
            )
            return response


class UsuarioDeleteView(AdminRequiredMixin, DeleteView):
    """
    Vista para eliminar usuarios
    """
    model = Usuario
    template_name = 'usuarios/eliminar.html'
    success_url = reverse_lazy('usuarios:lista')
    
    def delete(self, request, *args, **kwargs):
        usuario = self.get_object()
        nombre = usuario.get_full_name()
        
        # Verificar si puede eliminarse
        if usuario == request.user:
            messages.error(request, 'No puedes eliminar tu propio usuario.')
            return redirect('usuarios:lista')
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Usuario {nombre} eliminado correctamente.')
        return response


class PerfilView(LoginRequiredMixin, UpdateView):
    """
    Vista del perfil del usuario autenticado - permite ver y editar con validaciones completas
    """
    model = Usuario
    form_class = PerfilUpdateForm
    template_name = 'usuarios/perfil.html'
    success_url = reverse_lazy('usuarios:perfil')
    
    def get_object(self):
        """Retorna el usuario autenticado"""
        return self.request.user
    
    def get_form_kwargs(self):
        """Pasa la instancia del usuario al formulario para que se inicialice correctamente"""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs
    
    def form_valid(self, form):
        """Maneja el guardado exitoso del formulario"""
        response = super().form_valid(form)
        messages.success(
            self.request, 
            '¡Perfil actualizado correctamente! Todos los datos han sido validados y guardados.'
        )
        return response
    
    def form_invalid(self, form):
        """Maneja errores en el formulario"""
        messages.error(
            self.request,
            'Por favor, corrige los errores indicados en el formulario.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calcular edad si hay fecha de nacimiento
        if self.request.user.fecha_nacimiento:
            hoy = date.today()
            fecha_nac = self.request.user.fecha_nacimiento
            edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            context['edad'] = edad
        
        # Obtener o crear el perfil del usuario
        try:
            context['perfil'] = self.request.user.perfil
        except PerfilUsuario.DoesNotExist:
            context['perfil'] = PerfilUsuario.objects.create(
                usuario=self.request.user
            )
        
        return context


class EditarPerfilView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar el perfil del usuario
    """
    model = PerfilUsuario
    form_class = PerfilUsuarioForm
    template_name = 'usuarios/editar_perfil.html'
    success_url = reverse_lazy('usuarios:perfil')
    
    def get_object(self):
        """Obtiene o crea el perfil del usuario autenticado"""
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=self.request.user
        )
        return perfil


# Vistas de Recuperación de Contraseña
class RecuperarPasswordView(FormView):
    """
    Vista para solicitar recuperación de contraseña
    """
    template_name = 'usuarios/recuperar_password.html'
    success_url = reverse_lazy('usuarios:recuperar_password_enviado')
    
    def get_form_class(self):
        from .forms import RecuperarPasswordForm
        return RecuperarPasswordForm
    
    def form_valid(self, form):
        """Envía el email de recuperación"""
        email = form.cleaned_data['email']
        
        # Registrar intento de recuperación (para prevenir spam/ataques)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Intento de recuperación de contraseña para: {email}")
        
        try:
            usuario = Usuario.objects.get(email=email, is_active=True)
            
            # Generar token de recuperación
            token = default_token_generator.make_token(usuario)
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            
            # Crear enlace de recuperación
            reset_link = self.request.build_absolute_uri(
                f'/usuarios/restablecer-password/{uid}/{token}/'
            )
            
            # Enviar email (simulado por ahora)
            # En un entorno real, aquí enviarías el email
            self.enviar_email_recuperacion(usuario, reset_link)
            
            messages.success(
                self.request,
                f'Se ha enviado un enlace de recuperación a {email}'
            )
            
        except Usuario.DoesNotExist:
            # No revelar si el email existe o no por seguridad
            messages.success(
                self.request,
                'Si el correo existe en nuestro sistema, recibirás un enlace de recuperación.'
            )
        
        return super().form_valid(form)
    
    def enviar_email_recuperacion(self, usuario, reset_link):
        """
        Envía el email de recuperación de contraseña
        En desarrollo, solo imprime el enlace
        """
        asunto = 'Recuperación de Contraseña - Sistema de Gestión Académica'
        mensaje = f"""
        Hola {usuario.first_name},
        
        Has solicitado recuperar tu contraseña. Haz clic en el siguiente enlace para establecer una nueva contraseña:
        
        {reset_link}
        
        Este enlace expirará en 30 minutos.
        
        Si no solicitaste este cambio, puedes ignorar este mensaje.
        
        Saludos,
        Sistema de Gestión Académica
        """
        
        # En desarrollo, imprimir el enlace en la consola
        print(f"\n{'='*50}")
        print("EMAIL DE RECUPERACIÓN DE CONTRASEÑA")
        print(f"{'='*50}")
        print(f"Para: {usuario.email}")
        print(f"Asunto: {asunto}")
        print(f"Enlace de recuperación: {reset_link}")
        print(f"{'='*50}\n")
        
        # Enviar email real
        try:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )
            print(f"✅ Email enviado correctamente a {usuario.email}")
        except Exception as e:
            print(f"❌ Error al enviar email: {e}")
            # Aún así mostramos el enlace en consola como respaldo
            pass


class RecuperarPasswordEnviadoView(TemplateView):
    """
    Vista que confirma que se ha enviado el email de recuperación
    """
    template_name = 'usuarios/recuperar_password_enviado.html'


class RestablecerPasswordView(FormView):
    """
    Vista para establecer nueva contraseña usando el token
    """
    template_name = 'usuarios/restablecer_password.html'
    success_url = reverse_lazy('usuarios:password_restablecido')
    
    def get_form_class(self):
        from .forms import RestablecerPasswordForm
        return RestablecerPasswordForm
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el token sea válido"""
        self.usuario = self.get_usuario()
        
        if not self.usuario:
            messages.error(request, 'El enlace de recuperación no es válido o ha expirado.')
            return redirect('usuarios:login')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_usuario(self):
        """Obtiene el usuario del token"""
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs['uidb64']))
            usuario = Usuario.objects.get(pk=uid, is_active=True)
            
            # Verificar que el token sea válido
            if default_token_generator.check_token(usuario, self.kwargs['token']):
                return usuario
                
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            pass
        
        return None
    
    def form_valid(self, form):
        """Establece la nueva contraseña"""
        nueva_password = form.cleaned_data['new_password1']
        
        # Registrar cambio de contraseña
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Contraseña restablecida para usuario: {self.usuario.username} ({self.usuario.email})")
        
        # Cambiar contraseña
        self.usuario.set_password(nueva_password)
        
        # Si debe cambiar password, ya no es necesario
        if hasattr(self.usuario, 'debe_cambiar_password'):
            self.usuario.debe_cambiar_password = False
        
        self.usuario.save()
        
        # Invalidar todas las sesiones activas del usuario por seguridad
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(self.usuario.pk):
                session.delete()
        
        # Enviar email de notificación de cambio de contraseña
        self.enviar_notificacion_cambio(self.usuario)
        
        messages.success(
            self.request,
            'Tu contraseña ha sido actualizada exitosamente. Por seguridad, todas tus sesiones activas han sido cerradas. Ya puedes iniciar sesión con tu nueva contraseña.'
        )
        
        return super().form_valid(form)
    
    def enviar_notificacion_cambio(self, usuario):
        """Envía email notificando que la contraseña fue cambiada"""
        asunto = 'Contraseña Actualizada - Sistema de Gestión Académica'
        mensaje = f"""
Hola {usuario.first_name},

Te confirmamos que tu contraseña ha sido actualizada exitosamente.

Si no realizaste este cambio, contacta inmediatamente al administrador del sistema.

Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Saludos,
Sistema de Gestión Académica
        """
        
        try:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=True,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar notificación de cambio de contraseña: {e}")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.usuario
        return context


class PasswordRestablecidoView(TemplateView):
    """
    Vista que confirma que la contraseña ha sido restablecida
    """
    template_name = 'usuarios/password_restablecido.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Perfil actualizado correctamente.')
        return response
