import datetime

from django import forms
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

from .models import Lesson
from CalendarApi.constraints import (
    С_morning_time, С_morning_time_markup, C_evening_time_markup,
    C_evening_time, C_salary_common, C_salary_high, C_salary_max, C_timedelta,
    C_datedelta
)


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
                'value': C_salary_common
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

    def is_valid(self, request, form):
        """
        1. checking the overlap of lessons on each other - for all
        (lesson duration = 1 hour)
        2. check for too early and late lessons by day -  for users only
        3. checking for too early and late lessons by the hour - for users only
        4. checking cost of too early and late lessons by the hour - users only
        5. checking the lead time - for users only
        (you can not add a lesson earlier than 6 hours)
        6. checking for cost limits (700<=salary) - for users only
        """

        salary = form['salary'].value()
        time = form['time'].value()
        date = form['date'].value()

        try:
            salary = int(salary)
        except BaseException:
            messages.error(request,
                           'Payment must be integer')
            return False

        try:
            time = datetime.datetime.strptime(time, r"%H:%M").time()
        except BaseException:
            try:
                time = datetime.datetime.strptime(time, r"%H:%M:%S").time()
            except BaseException:
                messages.error(
                    request,
                    "Time must be in 'hours:minutes' or "
                    "'hours:minutes:seconds' format"
                )
                return False

        try:
            date = datetime.datetime.strptime(date, r"%Y-%m-%d").date()
        except BaseException:
            messages.error(request,
                           "Date must be in 'year-month-day' format")
            return False

        dt_now = datetime.datetime.now()

        if salary < C_salary_common:
            messages.error(
                request,
                f'The minimum cost of a lesson is {C_salary_common}'
            )
            return False
        elif salary > C_salary_max:
            messages.error(
                request,
                f'Perfaps you made a mistake in the cost ({salary}₽)'
            )
            return False

        if date < dt_now.date():
            messages.error(
                request,
                f"The date {date} has already arrived"
            )
            return False
        elif date > (dt_now + C_datedelta).date():
            messages.error(
                request,
                f"Please don't book a lesson earlier then {C_datedelta} "
                f"days in advace"
            )
            return False

        if datetime.datetime.combine(date, time) < dt_now + C_timedelta:
            messages.error(
                request,
                f"Please, sign up for a lesson {C_timedelta} hours before to "
                f"start"
            )
            return False

        if time < С_morning_time:
            messages.error(request, f"The time {time} is too early")
            return False
        elif С_morning_time <= time < С_morning_time_markup:
            if salary < C_salary_high:
                messages.error(
                    request,
                    f"in the morning ({С_morning_time}-{С_morning_time_markup}"
                    f" hours) the cost of the lesson is {C_salary_high}"
                )
                return False

        elif C_evening_time_markup <= time < C_evening_time:
            if salary < C_salary_high:
                messages.error(
                    request,
                    f"in the evening ({C_evening_time_markup}-{C_evening_time}"
                    f" hours) the cost of the lesson is {C_salary_high}"
                )
                return False
        elif time > C_evening_time:
            messages.error(request, f"The time {time} is too late")
            return False

        queryset = Lesson.objects.filter(date=date).values_list('time')
        times = [item[0] for item in queryset]

        for t1 in times:
            t2 = datetime.time(t1.hour+1, t1.minute, t1.second)
            if t1 <= time < t2:
                messages.error(
                    request,
                    f"Some lesson is already scheduled for {t1} that day"
                )
                return False

        return super().is_valid()
