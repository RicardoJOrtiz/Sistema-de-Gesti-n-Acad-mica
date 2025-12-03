# Configuración de Gmail para envío de emails

**Última actualización:** 2 de diciembre de 2025  
**Estado:** ✅ Configurado y funcionando

---

## 📧 Estado Actual de la Configuración

El sistema está configurado para enviar emails a través de Gmail SMTP. La configuración se encuentra en el archivo `.env` y es utilizada por `settings.py`.

### ⚙️ Configuración Actual (en `.env`):
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ricardo@gmail.com
EMAIL_HOST_PASSWORD=zziu puco dket ypote  # Contraseña de aplicación Gmail
DEFAULT_FROM_EMAIL=Sistema Académico <ricardo@gmail.com>
```

**⚠️ IMPORTANTE:** Si vas a subir el proyecto a GitHub público, considera:
1. Generar nueva contraseña de aplicación
2. Usar credenciales de prueba
3. O comentar estas credenciales y documentar cómo configurarlas

---

## 🔧 Pasos para configurar envío de emails desde Gmail

### 1. Habilitar verificación en dos pasos
   - Ve a https://myaccount.google.com/security
   - Habilita "Verificación en dos pasos"

### 2. Crear Contraseña de Aplicación
   - Ve a https://myaccount.google.com/apppasswords
   - Selecciona "Correo"
   - Selecciona "Otro (nombre personalizado)"
   - Escribe "Sistema Académico Django"
   - Copia la contraseña de 16 caracteres

### 3. Configurar archivo .env
   ```env
   EMAIL_HOST_USER=tu_email@gmail.com
   EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # Contraseña de aplicación
   ```

### 4. Reiniciar servidor
   ```bash
   python manage.py runserver
   ```

---

## 🔒 Seguridad

✅ El archivo `.env` está en `.gitignore`  
⚠️ Cambiar EMAIL_HOST_PASSWORD antes de repositorio público

---

**Última actualización:** 2 de diciembre de 2025
