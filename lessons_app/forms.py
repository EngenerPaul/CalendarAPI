import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext as _

from .models import Lesson
from CalendarApi.constraints import (
    С_morning_time, С_morning_time_markup, C_evening_time_markup,
    C_evening_time, C_salary_common, C_salary_high, C_salary_max, C_timedelta,
    C_datedelta, C_lesson_threshold
)


class RegisterUserForm(forms.Form):
    """Form for registration
    Use in views - CustomRegistration, template - registration.html"""

    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your login'),
            'style': 'margin-bottom: 10px'
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your password'),
            'style': 'margin-bottom: 10px'
        })
    )
    first_name = forms.CharField(
        label=_('Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your name'),
            'style': 'margin-bottom: 10px'
        })
    )
    phone = forms.CharField(
        label=_('Phone'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '89001234567',
            'style': 'margin-bottom: 10px'
        }),
        required=False
    )
    telegram = forms.CharField(
        label='Telegram',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '@nickname'
        }),
        required=False
    )

    def is_valid(self, request, form) -> bool:

        # username doen't contain spaces
        if len(form['username'].value().split()) > 1:
            messages.error(request, _("Username doen't contain spaces"))
            return False

        # password doen't contain spaces
        if len(form['password'].value().split()) > 1:
            messages.error(request, _("Password doen't contain spaces"))
            return False

        # phone or telegram must exist
        if form['phone'].value() == form['telegram'].value() == '':
            messages.error(
                request,
                _('You must provide a phone number or telegram nickname')
            )
            return False

        # check phone format
        if form['phone'].value() != '':
            try:
                int(form['phone'].value())
            except BaseException:
                messages.error(request, _("Phone number must be digits only"))
                return False
            if len(form['phone'].value()) != 11:
                messages.error(
                    request,
                    message=_("Phone number must contain 11 digits")
                )
                return False

        # check telegram format
        if form['telegram'].value() != '':
            if form['telegram'].value()[0] != '@':
                messages.error(
                    request,
                    message=_("Telegram nickname must start with '@..'")
                )
                return False
            if len(form['telegram'].value().split()) > 1:
                messages.error(
                    request,
                    message=_("Telegram nickname doen't contain spaces")
                )
                return False

        return super().is_valid()


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
                'placeholder'] = _('Enter your username')
            self.fields['password'].widget.attrs[
                'placeholder'] = _('Enter your password')


class AddLessonForm(forms.ModelForm):
    """ Create a new lesson by students """

    class Meta:
        model = Lesson
        fields = ('theme', 'salary', 'time', 'date')
        labels = {
            'theme': _('Theme'),
            'salary': _('Pay'),
            'time': _('Time'),
            'date': _('Date')
        }
        widgets = {
            'theme': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('optional')
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
        7. check of lesson cost when numbers lesson todate is big - for users
        """

        salary = form['salary'].value()
        time = form['time'].value()
        date = form['date'].value()

        try:
            salary = int(salary)
        except BaseException:
            messages.error(request,
                           _('Payment must be integer'))
            return False

        try:
            time = datetime.datetime.strptime(time, r"%H:%M").time()
        except BaseException:
            try:
                time = datetime.datetime.strptime(time, r"%H:%M:%S").time()
            except BaseException:
                messages.error(
                    request,
                    _("Time must be in 'hours:minutes' or "
                      "'hours:minutes:seconds' format")
                )
                return False

        try:
            date = datetime.datetime.strptime(date, r"%Y-%m-%d").date()
        except BaseException:
            messages.error(request,
                           _("Date must be in 'year-month-day' format"))
            return False

        dt_now = datetime.datetime.now()

        if salary < C_salary_common:
            messages.error(
                request,
                _('The minimum cost of a lesson is {}').format(C_salary_common)
            )
            return False
        elif salary > C_salary_max:
            messages.error(
                request,
                _('Perfaps you made a mistake in the cost')
            )
            return False

        if date < dt_now.date():
            messages.error(
                request,
                _("The date {} has already arrived").format(date)
            )
            return False
        elif date > (dt_now + C_datedelta).date():
            messages.error(
                request,
                _("Please don't book a lesson earlier then {} "
                  "days in advace").format(C_datedelta.days)
            )
            return False

        if datetime.datetime.combine(date, time) < dt_now + C_timedelta:
            messages.error(
                request,
                _("Please, sign up for a lesson {} hours before to "
                  "start").format(C_timedelta)
            )
            return False

        if time < С_morning_time:
            messages.error(request, _("The time {} is too early").format(time))
            return False
        elif С_morning_time <= time < С_morning_time_markup:
            if salary < C_salary_high:
                messages.error(
                    request,
                    _("in the morning ({0}-{1} hours) the cost of the lesson"
                      " is {2}").format(
                        С_morning_time, С_morning_time_markup, C_salary_high
                    )
                )
                return False

        elif C_evening_time_markup <= time < C_evening_time:
            if salary < C_salary_high:
                messages.error(
                    request,
                    _("in the evening ({0}-{1} hours) the cost of the lesson"
                      " is {2}").format(
                          C_evening_time_markup, C_evening_time, C_salary_high
                      )
                )
                return False
        elif time > C_evening_time:
            messages.error(request, _("The time {} is too late").format(time))
            return False

        queryset = Lesson.objects.filter(date=date).values_list('time')
        times = [item[0] for item in queryset]

        for t1 in times:
            t2 = datetime.time(t1.hour+1, t1.minute, t1.second)
            if t1 <= time < t2:
                messages.error(
                    request,
                    _("Some lesson is already scheduled for {} that "
                      "day").format(t1)
                )
                return False

        if len(queryset) >= C_lesson_threshold:
            if salary < C_salary_high:
                messages.error(
                    request,
                    _("Amount of lessons today is greater than or equel "
                      "to {0}. Lesson cost is {1} ₽").format(
                        C_lesson_threshold, C_salary_high
                    )
                )
                return False

        return super().is_valid()


class AddLessonAdminForm(forms.ModelForm):
    """ Create a new lesson for students by admin """

    class Meta:
        model = Lesson
        fields = ('student', 'theme', 'salary', 'time', 'date')
        labels = {
            'student': _('Student'),
            'theme': _('Theme'),
            'salary': _('Pay'),
            'time': _('Time'),
            'date': _('Date')
        }
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control',
                'size': 10
            }),
            'theme': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('optional')
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
        """ Checking the overlap of lessons on each other - for all
        (lesson duration = 1 hour) """

        salary = form['salary'].value()
        time = form['time'].value()
        date = form['date'].value()

        try:
            salary = int(salary)
        except BaseException:
            messages.error(request,
                           _('Payment must be integer'))
            return False

        try:
            time = datetime.datetime.strptime(time, r"%H:%M").time()
        except BaseException:
            try:
                time = datetime.datetime.strptime(time, r"%H:%M:%S").time()
            except BaseException:
                messages.error(
                    request,
                    _("Time must be in 'hours:minutes' or "
                      "'hours:minutes:seconds' format")
                )
                return False

        try:
            date = datetime.datetime.strptime(date, r"%Y-%m-%d").date()
        except BaseException:
            messages.error(request,
                           _("Date must be in 'year-month-day' format"))
            return False

        if form['student'].value() == '':
            messages.error(
                request,
                _("Please, select a student")
            )
            return False

        queryset = Lesson.objects.filter(date=date).values_list('time')
        times = [item[0] for item in queryset]

        for t1 in times:
            t2 = datetime.time(t1.hour+1, t1.minute, t1.second)
            if t1 <= time < t2:
                messages.error(
                    request,
                    _("Some lesson is already scheduled for {} that "
                      "day").format(t1)
                )
                return False

        dt_now = datetime.datetime.now()
        if date > (dt_now + C_datedelta).date():
            messages.error(
                request,
                _("Please don't book a lesson earlier then {} "
                  "days in advace").format(C_datedelta.days)
            )
            return False

        return super().is_valid()
