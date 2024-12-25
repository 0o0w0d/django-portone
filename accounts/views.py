from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required

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


class LogoutView(LogoutView):
    next_page = "login"


signup = SignupView.as_view()
login = LoginView.as_view()
logout = LogoutView.as_view()


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
