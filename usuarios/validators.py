"""
Validadores personalizados de contraseñas
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class PasswordComplexityValidator:
    """
    Validador que requiere:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un símbolo especial
    """
    
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("La contraseña debe tener al menos 8 caracteres."),
                code='password_too_short',
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra minúscula."),
                code='password_no_lower',
            )
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un número."),
                code='password_no_digit',
            )
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un símbolo especial (!@#$%^&*()_+-=[]{};:'\",.<>?/\\|`~)."),
                code='password_no_symbol',
            )
    
    def get_help_text(self):
        return _(
            "Tu contraseña debe tener al menos 8 caracteres, incluyendo: "
            "una mayúscula, una minúscula, un número y un símbolo especial."
        )
