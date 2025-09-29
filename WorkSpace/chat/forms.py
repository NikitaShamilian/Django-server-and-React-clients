from django import forms
from .models import Profile
from django.contrib.auth.models import User

class createUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password"]


class profileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio"]