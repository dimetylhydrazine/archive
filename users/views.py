from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserLoginForm
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {"form": form})

class UserLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')