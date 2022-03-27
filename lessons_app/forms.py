from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

from .models import Lesson


class RegisterUserForm(forms.ModelForm):
    """Form for registration
    Use in views - CustomRegistration, template - registration.html"""

    class Meta:
        model = User
        fields = ('username', 'first_name', 'password')
        labels = {
            'username': 'Login',
            'first_name': 'Name',
            'password': 'Password',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your login'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your name'
            }),
            'password': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your password'
            })
        }
        help_texts = {
            'username': None,
        }

    # .\venv\Lib\site-packages\django\contrib\auth\forms.py
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class AuthUserForm(AuthenticationForm, forms.ModelForm):
    """Form for authentication.
    Use in views - CustomLoginView, template - login.html"""
    # AuthenticationForm needed for using authentication

    class Meta:
        model = User
        fields = ('username', 'password')

        # labels = {...}  doesn't work!
        # widgets = {...}  doesn't work!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields['username'].widget.attrs[
                'placeholder'] = 'Укажите Ваше имя'
            self.fields['password'].widget.attrs[
                'placeholder'] = 'Введите пароль'


class AddLessonForm(forms.ModelForm):

    class Meta:
        model = Lesson
        fields = ('theme', 'salary', 'time', 'date')
        labels = {
            'theme': 'Theme',
            'salary': 'Pay',
            'time': 'Time',
            'date': 'Date'
        }
        widgets = {
            'theme': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'optional'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 700
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': '00:00:00'
            }),
            'date': forms.DateInput(format=r'%d.%m.%Y', attrs={
                'class': 'form-control',
                'placeholder': '2022-12-31'
            }),
        }
