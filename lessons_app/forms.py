import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext as _

from .models import Lesson
from CalendarApi.constraints import (
    С_morning_time, C_evening_time,  C_timedelta,  C_datedelta
)
from .caches import get_blocked_time


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


class AddLessonForm(forms.Form):
    """ Create a new lesson by student """

    time = forms.IntegerField(
        label=_('Time'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '00:00',
            'value': 15
        })
    )

    weekdays = {
        'Monday': _('Monday'),
        'Tuesday': _('Tuesday'),
        'Wednesday': _('Wednesday'),
        'Thursday': _('Thursday'),
        'Friday': _('Friday'),
        'Saturday': _('Saturday'),
        'Sunday': _('Sunday'),
    }
    choice = []
    for i in range(C_datedelta.days+1):
        if i == 0:
            date = datetime.date.today() + datetime.timedelta(days=i)
            day_title = (f"{_('Today')}, "
                         f"{datetime.datetime.strftime(date, r'%d-%m')}")
            choice.append((date, day_title))
            continue
        date = datetime.date.today() + datetime.timedelta(days=i)
        day_title = (f"{weekdays[date.strftime('%A')]}, "
                     f"{datetime.datetime.strftime(date, r'%d-%m')}")
        choice.append((date, day_title))
    date = forms.CharField(
        label=_('Date'),
        widget=forms.Select(choices=choice, attrs={
            'class': 'form-control'
        })
    )

    def is_valid(self, request, form):
        try:
            time = str(form['time'].value()).split(':')[0]
            time = datetime.datetime.strptime(time, r"%H").time()
        except ValueError:
            messages.error(
                request,
                _("Time must be in 'hours' or "
                    "'hours:minutes' format")
            )
            return False

        date = datetime.datetime.strptime(
            form['date'].value(),
            r"%Y-%m-%d"
        ).date()

        dt_now = datetime.datetime.now()

        # sign up is impossible for past date or today + 8 days
        if datetime.datetime.combine(date, time) < dt_now:
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

        # sign up is impossible for next 3 hours
        if datetime.datetime.combine(date, time) < dt_now + C_timedelta:
            messages.error(
                request,
                _("Please, sign up for a lesson {} hours before to "
                  "start").format(C_timedelta)
            )
            return False

        # constraint of working hours (8-23)
        if time < С_morning_time:
            messages.error(request, _("The time {} is too early").format(time))
            return False
        elif time > C_evening_time:
            messages.error(request, _("The time {} is too late").format(time))
            return False

        # free time check
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

        # check blocked time overlap
        blocked_time = get_blocked_time()
        if blocked_time:
            if date in blocked_time.keys():
                for times in blocked_time[date]:
                    if (times[0] <= time < times[1]) or \
                            (time == times[1] == datetime.time(23)):
                        messages.error(
                            request,
                            _("This time is blocked")
                        )
                        return False

        # super consist variable because it is used by AddLessonAdminForm class
        return super(forms.Form, self).is_valid()


class AddLessonAdminForm(forms.Form):
    """ Create a new lesson for students by admin """

    students = User.objects.filter(is_staff=False, is_active=True)
    choice = []
    for student in students:
        choice.append((student.id, student.first_name))
    student = forms.CharField(
        label=_('Student'),
        widget=forms.Select(
            choices=choice,
            attrs={
                'class': 'form-control',
                'size': 10
            }
        )
    )
    time = forms.IntegerField(
        label=_('Time'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '00:00',
            'value': 15
        })
    )

    weekdays = {
        'Monday': _('Monday'),
        'Tuesday': _('Tuesday'),
        'Wednesday': _('Wednesday'),
        'Thursday': _('Thursday'),
        'Friday': _('Friday'),
        'Saturday': _('Saturday'),
        'Sunday': _('Sunday'),
    }
    choice = []
    for i in range(C_datedelta.days+1):
        if i == 0:
            date = datetime.date.today() + datetime.timedelta(days=i)
            day_title = (f"{_('Today')}, "
                         f"{datetime.datetime.strftime(date, r'%d-%m')}")
            choice.append((date, day_title))
            continue
        date = datetime.date.today() + datetime.timedelta(days=i)
        day_title = (f"{weekdays[date.strftime('%A')]}, "
                     f"{datetime.datetime.strftime(date, r'%d-%m')}")
        choice.append((date, day_title))
    date = forms.CharField(
        label=_('Date'),
        widget=forms.Select(choices=choice, attrs={
            'class': 'form-control'
        })
    )
    salary = forms.IntegerField(
        label=_('Cost'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'value': 1000
        })
    )

    def is_valid(self, request, form):
        try:
            time = str(form['time'].value()).split(':')[0]
            time = datetime.datetime.strptime(time, r"%H").time()
        except ValueError:
            messages.error(
                request,
                _("Time must be in 'hours' or "
                    "'hours:minutes' format")
            )
            return False

        date = datetime.datetime.strptime(
            form['date'].value(),
            r"%Y-%m-%d"
        ).date()

        if form['student'].value() == '':
            messages.error(
                request,
                _("Please, select a student")
            )
            return False

        # check blocked time overlap
        blocked_time = get_blocked_time()
        if blocked_time:
            if date in blocked_time.keys():
                for times in blocked_time[date]:
                    if (times[0] <= time < times[1]) or \
                            (time == times[1] == datetime.time(23)):
                        messages.error(
                            request,
                            _("This time is blocked")
                        )
                        return False

        # uses created validator from AddLessonForm class
        return AddLessonForm.is_valid(self, request, form)


class TimeBlockerAPForm(forms.Form):
    """ Form for the time blocker in the admin panel """

    weekdays = {
        'Monday': _('Monday'),
        'Tuesday': _('Tuesday'),
        'Wednesday': _('Wednesday'),
        'Thursday': _('Thursday'),
        'Friday': _('Friday'),
        'Saturday': _('Saturday'),
        'Sunday': _('Sunday'),
    }
    choice = []
    for i in range(C_datedelta.days+1):
        if i == 0:
            date = datetime.date.today() + datetime.timedelta(days=i)
            day_title = (f"{_('Today')}, "
                         f"{datetime.datetime.strftime(date, r'%d-%m')}")
            choice.append((date, day_title))
            continue
        date = datetime.date.today() + datetime.timedelta(days=i)
        day_title = (f"{weekdays[date.strftime('%A')]}, "
                     f"{datetime.datetime.strftime(date, r'%d-%m')}")
        choice.append((date, day_title))
    date = forms.CharField(
        label=_('Date'),
        widget=forms.Select(choices=choice, attrs={
            'class': 'form-control'
        })
    )
    start_time = forms.IntegerField(
        label=_('Start time'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '00:00',
            'value': 8
        })
    )
    end_time = forms.IntegerField(
        label=_('End time'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '00:00',
            'value': 23
        })
    )

    def is_valid(self, request) -> bool:
        date = self['date'].value()
        start_time = self['start_time'].value()
        end_time = self['end_time'].value()
        date = datetime.datetime.strptime(date, r'%Y-%m-%d').date()
        start_time = datetime.datetime.strptime(start_time, r'%H').time()
        end_time = datetime.datetime.strptime(end_time, r'%H').time()

        # check of times
        if start_time > end_time:
            messages.error(
                request,
                _("'Start time' must be earlier than 'End time'")
            )
            return False
        elif start_time == end_time:
            messages.error(
                request,
                _("'Start time' and 'End time' can't be equal")
            )
            return False

        # checking if block overlap
        blocked_time = get_blocked_time()
        if blocked_time:
            if date in blocked_time.keys():
                for times in blocked_time[date]:
                    if start_time >= times[0] and start_time < times[1] or \
                            end_time > times[0] and end_time <= times[1]:
                        messages.error(
                            request,
                            _("The new block overlaps the existing one")
                        )
                        return False

        # check for future date (date > today)
        today = datetime.date.today()
        if date < today:
            messages.error(
                request,
                _("Date can't be earlier than today")
            )
            return False

        # check for date in the current period (8 day)
        if date > today + C_datedelta:
            messages.error(
                request,
                _("You are creating the block too early")
            )
            return False

        # check for non-existence of lessons
        lessons = Lesson.objects.filter(date=date).values('time')
        for lesson in lessons:
            if start_time <= lesson['time'] < end_time:
                messages.error(
                    request,
                    _("Your block overlaps an existing lesson")
                )
                return False

        return super().is_valid()
