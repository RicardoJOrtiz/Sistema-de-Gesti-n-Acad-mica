# Sistema de Gestión Académica

Trabajo final de la materia Desarrollo de Sistemas Web. Un sistema web desarrollado en Django para la gestión académica de instituciones educativas.

Desarrollado por Ortiz Ricardo.



## Características Principales

### Tecnologías Utilizadas

- **Python 3.8+** - Lenguaje de programación
- **Django 5.2.6** - Framework web
- **SQLite** - Base de datos (desarrollo)
- **Bootstrap 5** - Framework CSS
- **django-bootstrap5** - Integración con Bootstrap

### Funcionalidades Implementadas

#### Gestión de Usuarios

- ✅ Modelo de usuario personalizado con roles
- ✅ Autenticación con DNI o email
- ✅ Roles diferenciados: Administrador, Alumno, Docente, Preceptor, Invitado
- ✅ Cambio obligatorio de contraseña en el primer acceso
- ✅ Gestión de perfiles de usuario

#### Gestión Académica

- ✅ CRUD completo para Carreras, Materias, Alumnos
- ✅ Sistema de inscripciones con validaciones
- ✅ Control de cupos máximos por materia
- ✅ Validaciones de integridad referencial

#### Principios de POO Implementados

- ✅ **Herencia**: Clase abstracta `Persona` para `Alumno`
- ✅ **Encapsulamiento**: Métodos privados y propiedades
- ✅ **Abstracción**: Managers personalizados para lógica de negocio
- ✅ **Interfaces**: Métodos abstractos en modelos base

#### Funcionalidades de Filtrado

- ✅ Filtrar materias por carrera
- ✅ Ver materias con cupo disponible
- ✅ Buscar usuarios por nombre, DNI o email
- ✅ Filtrar alumnos por carrera

## Estructura del Proyecto

```
gestion_academica/
├── gestion_academica/          # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── usuarios/                   # App de usuarios y autenticación
│   ├── models.py              # Usuario personalizado y Perfil
│   ├── views.py               # Vistas de autenticación y CRUD
│   ├── forms.py               # Formularios personalizados
│   └── urls.py
├── carreras/                   # App de carreras
│   ├── models.py              # Modelo Carrera
│   ├── views.py               # CRUD de carreras
│   └── urls.py
├── materias/                   # App de materias
│   ├── models.py              # Modelo Materia
│   ├── views.py               # CRUD de materias
│   └── urls.py
├── alumnos/                    # App de alumnos
│   ├── models.py              # Modelo Persona (abstracto) y Alumno
│   ├── views.py               # CRUD de alumnos
│   └── urls.py
├── inscripciones/              # App de inscripciones
│   ├── models.py              # Modelo Inscripcion con Manager
│   ├── views.py               # Gestión de inscripciones
│   └── urls.py
├── templates/                  # Templates HTML
│   ├── base.html              # Template base con Bootstrap
│   └── home.html              # Página de inicio
└── static/                     # Archivos estáticos
    └── css/
        └── custom.css         # Estilos personalizados
```

## Instalación y Configuración

### 1. Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 2. Clonar el proyecto

```bash
git clone <url-del-repositorio>
cd gestion_academica
```

### 3. Crear entorno virtual

```bash
python -m venv .venv
```

### 4. Activar entorno virtual

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux/Mac:**

```bash
source .venv/bin/activate
```

### 5. Instalar dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install django>=5.2 Pillow django-bootstrap5 python-decouple unidecode
```

### 6. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Configuración de Email (Opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password
DEFAULT_FROM_EMAIL=Sistema Académico <tu-email@gmail.com>
```

### 7. Aplicar migraciones

```bash
python manage.py migrate
```

### 8. Crear usuario administrador semilla

```bash
python manage.py crear_admin_semilla
```

Esto creará un usuario administrador con las siguientes credenciales:
- **Usuario:** admin
- **Contraseña:** admin123
- **Email:** admin@sistema.com

**⚠️ IMPORTANTE:** Cambia la contraseña después del primer login.

### 9. Ejecutar el servidor

```bash
python manage.py runserver
```

El sistema estará disponible en: http://127.0.0.1:8000/

## Usuarios del Sistema

### Roles y Permisos

| Rol               | Permisos                                                                   |
| ----------------- | -------------------------------------------------------------------------- |
| **Administrador** | CRUD completo de usuarios, carreras, materias, alumnos e inscripciones     |
| **Alumno**        | Ver oferta académica, inscribirse/darse de baja de materias, ver sus datos |
| **Invitado**      | Solo ver carreras y materias (sin edición ni inscripción)                  |
| **Docente**       | Ver sus materias y listas de alumnos (solo visual)                         |
| **Preceptor**     | Gestionar inscripciones (solo visual)                                      |

### Datos de Prueba

Para crear usuarios de prueba, usar el panel de administración de Django:

1. Acceder a http://127.0.0.1:8000/admin/
2. Crear usuarios con diferentes roles
3. La contraseña inicial será el DNI del usuario
4. El usuario deberá cambiarla en el primer acceso

## Validaciones Implementadas

### Restricciones Lógicas

- ❌ No eliminar carreras con materias o alumnos asociados
- ❌ No eliminar materias con inscripciones activas
- ❌ No permitir inscripciones duplicadas
- ❌ No permitir inscripciones sin cupo disponible
- ❌ Validar que materias pertenezcan a la carrera del alumno

### Validaciones de Formularios

- ✅ Campos obligatorios
- ✅ Formato de email válido
- ✅ DNI único (7-8 dígitos numéricos)
- ✅ Formato de teléfono
- ✅ Unicidad de nombres de materias por carrera

## Casos de Uso Principales

### Como Administrador

1. Iniciar sesión en el sistema
2. Gestionar usuarios (crear, editar, eliminar)
3. Administrar carreras y materias
4. Ver todas las inscripciones
5. Gestionar alumnos

### Como Alumno

1. Iniciar sesión con DNI y email
2. Cambiar contraseña (obligatorio en primer acceso)
3. Ver oferta académica
4. Inscribirse a materias disponibles
5. Darse de baja de materias
6. Ver estado de sus inscripciones

### Como Invitado

1. Ver listado de carreras
2. Consultar materias por carrera
3. Ver información general del sistema

## Estructura de Base de Datos

### Modelos Principales

- **Usuario**: Modelo personalizado con campos adicionales y roles
- **PerfilUsuario**: Información adicional del perfil
- **Carrera**: Carreras académicas disponibles
- **Materia**: Materias de cada carrera con cupos
- **Persona**: Clase abstracta base (herencia)
- **Alumno**: Hereda de Persona, relacionado con Usuario
- **Inscripcion**: Tabla intermedia Alumno-Materia

### Relaciones

- Usuario 1:1 PerfilUsuario
- Usuario 1:1 Alumno
- Carrera 1:N Materia
- Carrera 1:N Alumno
- Alumno N:M Materia (a través de Inscripcion)

## Contacto y Soporte

**Ricardo Ortiz"**

- Centro Regional Universitario Ituzaingó




