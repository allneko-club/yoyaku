from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm
from django.core.exceptions import ValidationError


class AuthenticationForm(BaseAuthenticationForm):
    error_messages = {
        'invalid_login': '認証に失敗しました。ユーザIDまたはパスワードが間違っています。',
        'inactive': '認証に失敗しました。ユーザIDまたはパスワードが間違っています。',
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'ユーザID'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'パスワード'
        self.fields['password'].widget.attrs['class'] = 'form-control'

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(self.error_messages['invalid_login'], code='invalid_login')
