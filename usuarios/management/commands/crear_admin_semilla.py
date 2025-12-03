"""
Comando para crear usuario administrador semilla
Uso: python manage.py crear_admin_semilla
"""
from django.core.management.base import BaseCommand
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Crea un usuario administrador semilla para iniciar el sistema'

    def handle(self, *args, **kwargs):
        # Verificar si ya existe el usuario admin
        if Usuario.objects.filter(username='admin').exists():
            self.stdout.write(
                self.style.WARNING('⚠️  El usuario "admin" ya existe.')
            )
            return

        # Crear usuario administrador semilla
        try:
            admin = Usuario.objects.create_user(
                username='admin',
                email='admin@sistema.com',
                password='admin123',  # Contraseña temporal
                first_name='Administrador',
                last_name='del Sistema',
                dni='00000000',
                telefono='0000000000',
                rol='administrador',
                is_staff=True,
                is_superuser=True,
                debe_cambiar_password=True  # Forzar cambio de contraseña
            )

            self.stdout.write(
                self.style.SUCCESS('\n✅ Usuario administrador creado exitosamente!\n')
            )
            self.stdout.write(
                self.style.SUCCESS('=' * 60)
            )
            self.stdout.write(
                self.style.SUCCESS('   CREDENCIALES DE ACCESO')
            )
            self.stdout.write(
                self.style.SUCCESS('=' * 60)
            )
            self.stdout.write(f'   Usuario:     admin')
            self.stdout.write(f'   Contraseña:  admin123')
            self.stdout.write(f'   Email:       admin@sistema.com')
            self.stdout.write(
                self.style.SUCCESS('=' * 60)
            )
            self.stdout.write(
                self.style.WARNING('\n⚠️  IMPORTANTE: Cambie la contraseña después del primer login\n')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear usuario administrador: {e}')
            )
