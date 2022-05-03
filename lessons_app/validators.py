import datetime

from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError
from rest_framework.utils.representation import smart_repr

from CalendarApi.constraints import (
    С_morning_time, C_evening_time, C_timedelta, C_datedelta,
)
from .models import TimeBlock, Lesson


class RegistrationValidator():
    """ Check data for registration """

    def __init__(self):
        pass

    def __call__(self, attrs):

        # username doen't contain spaces
        if len(attrs['username'].split()) > 1:
            raise ValidationError(
                _("Username doen't contain spaces")
            )

        # password doen't contain spaces
        if len(attrs['password'].split()) > 1:
            raise ValidationError(
                _("Password doen't contain spaces")
            )

        # phone or telegram must exist
        if attrs['phone'] == attrs['telegram'] == '':
            raise ValidationError(
                _('You must provide a phone number or telegram nickname')
            )

        # check phone format
        if attrs['phone'] != '':
            try:
                int(attrs['phone'])
            except BaseException:
                raise ValidationError(_("Phone number must be digits only"))
            if len(attrs['phone']) != 11:
                raise ValidationError(_("Phone number must contain 11 digits"))

        # check telegram format
        if attrs['telegram'] != '':
            if attrs['telegram'][0] != '@':
                raise ValidationError(
                    _("Telegram nickname must start with '@..'")
                )
            if len(attrs['telegram'].split()) > 1:
                raise ValidationError(
                    _("Telegram nickname doen't contain spaces")
                )

    def __repr__(self):
        return 'RegistrationValidator class without queryset'


class AdminValidator():
    """ Сheck for non-intersection of lessons """

    def __init__(self, queryset):
        self.queryset = queryset

    def __call__(self, attrs):
        student = attrs['student']
        time = attrs['time']
        date = attrs['date']

        # free time check
        self.queryset = self.queryset.filter(date=date).values_list('time')
        times = [item[0] for item in self.queryset]
        for t1 in times:
            t2 = datetime.time(t1.hour+1, t1.minute, t1.second)
            if t1 <= time < t2:
                raise ValidationError(_(
                    "Some lesson is already scheduled for {} that day"
                ).format(t1))

        if student == '':
            raise ValidationError(_("Please, select a student"))

        # check blocked time overlap
        blocked_times = TimeBlock.objects.filter(date=date).values(
            'start_time', 'end_time')
        for blocked_time in blocked_times:
            if (blocked_time['start_time'] <= time < blocked_time['end_time']
                    or time == blocked_time['end_time'] == datetime.time(23)):
                raise ValidationError(_("This time is blocked"))

    def __repr__(self):
        return '<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        )


class UserValidator():
    """ Validation of creation (update) of new lesson by student """

    def __init__(self, queryset):
        self.queryset = queryset

    def __call__(self, attrs):
        time = attrs['time']
        date = attrs['date']
        dt_now = datetime.datetime.now()

        # sign up is impossible for past date or today + 8 days
        if date < dt_now.date():
            raise ValidationError(_("The date {} has already arrived").format(
                date))
        elif date > (dt_now + C_datedelta).date():
            raise ValidationError(
                _("Please don't book a lesson earlier then {} "
                  "days in advace").format(C_datedelta)
            )

        # sign up is impossible for next 3 hours
        if datetime.datetime.combine(date, time) < dt_now + C_timedelta:
            raise ValidationError(
                _("Please, sign up for a lesson {} hours before to "
                  "start").format(C_timedelta)
            )

        # constraint of working hours (8-23)
        if time < С_morning_time:
            raise ValidationError(_("The time {} is too early").format(time))
        elif time > C_evening_time:
            raise ValidationError(_("The time {} is too late").format(time))

        # free time check
        self.queryset = self.queryset.filter(date=date).values_list('time')
        times = [item[0] for item in self.queryset]
        for t1 in times:
            t2 = datetime.time(t1.hour+1, t1.minute, t1.second)
            if t1 <= time < t2:
                raise ValidationError(
                    _("Some lesson is already scheduled for "
                      "{} that day").format(t1)
                )

        # check blocked time overlap
        blocked_times = TimeBlock.objects.filter(date=date).values(
            'start_time', 'end_time')
        for blocked_time in blocked_times:
            if (blocked_time['start_time'] <= time < blocked_time['end_time']
                    or time == blocked_time['end_time'] == datetime.time(23)):
                raise ValidationError(_("This time is blocked"))

    def __repr__(self):
        return '<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        )


class TimeBlockValidator():
    """ Validator of Timeblock """

    def __init__(self, queryset):
        self.queryset = queryset

    def __call__(self, attrs):
        date = attrs['date']
        start_time = attrs['start_time']
        end_time = attrs['end_time']

        # check of times
        if start_time > end_time:
            raise ValidationError(
                _("'Start time' must be earlier than 'End time'")
            )
        elif start_time == end_time:
            raise ValidationError(
                _("'Start time' and 'End time' can't be equal")
            )

        # checking if block overlap
        blocked_times = self.queryset.filter(date=date).values(
            'start_time', 'end_time')
        for blocked_time in blocked_times:
            condition_1 = (blocked_time['start_time'] <= start_time
                           < blocked_time['end_time'])
            condition_2 = (blocked_time['start_time'] < end_time
                           < blocked_time['end_time'])
            condition_3 = (start_time < blocked_time['end_time']
                           and end_time > blocked_time['start_time'])
            if condition_1 or condition_2 or condition_3:
                raise ValidationError(
                    _("The new block overlaps the existing one")
                )

        # check for future date (date > today)
        today = datetime.date.today()
        if date < today:
            raise ValidationError(
                _("Date can't be earlier than today")
            )

        # check for date in the current period (8 day)
        if date > today + C_datedelta:
            raise ValidationError(
                _("You are creating the block too early")
            )

        # check for non-existence of lessons
        lessons = Lesson.objects.filter(date=date).values('time')
        for lesson in lessons:
            if start_time <= lesson['time'] < end_time:
                raise ValidationError(
                    _("Your block overlaps an existing lesson")
                )

    def __repr__(self):
        return '<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        )
