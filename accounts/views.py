from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView

from accounts.forms import LoginForm, SignupForm
from accounts.models import User


class SignupView(CreateView):
    model = User
    form_class = SignupForm
    template_name = "accounts/signup_form.html"
    success_url = reverse_lazy("login")


class LoginView(LoginView):
    template_name = "accounts/login_form.html"
    form_class = LoginForm


signup = SignupView.as_view()
login = LoginView.as_view()


def logout(request):
    pass


def profile(request):
    pass
