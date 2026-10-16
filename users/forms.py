from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class UserRegisterForm(UserCreationForm):

    email = forms.EmailField(required=True, max_length=254)

    class Meta:
        model = User
        fields = ['nickname', 'email']

class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True}),)
