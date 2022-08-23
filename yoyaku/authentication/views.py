from django.contrib.auth.views import LogoutView, LoginView

from .forms import AuthenticationForm


class UserLoginView(LoginView):
    authentication_form = AuthenticationForm
    template_name = 'accounts/login.html'


class UserLogoutView(LogoutView):
    template_name = 'accounts/login.html'
