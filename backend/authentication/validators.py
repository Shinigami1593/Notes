from django.contrib.auth.password_validation import CommonPasswordValidator, MinimumLengthValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import check_password
from django.conf import settings
import re


class PasswordComplexityValidator:
    """
    Custom password validator for complexity requirements
    OWASP recommendations:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."),
                code='password_no_special',
            )
    
    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )


def check_password_history(user, new_password):
    """
    Check if password was used recently
    Returns True if password is acceptable (not in history)
    Returns False if password was used before
    """
    from .models import PasswordHistory
    
    history_count = getattr(settings, 'PASSWORD_HISTORY_COUNT', 5)
    password_history = PasswordHistory.objects.filter(user=user).order_by('-created_at')[:history_count]
    
    for old_password in password_history:
        if check_password(new_password, old_password.password_hash):
            return False
    
    return True