import datetime

from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError
from rest_framework.utils.representation import smart_repr

from CalendarApi.constraints import (
    С_morning_time, С_morning_time_markup, C_evening_time_markup,
    C_evening_time, C_salary_common, C_salary_high, C_salary_max, C_timedelta,
    C_datedelta, C_lesson_threshold
)


class AdminValidator():
    """ Сheck for non-intersection of lessons """

    def __init__(self, queryset):
        self.queryset = queryset
        self.message = _("Some lesson is already scheduled for {} that day")

    def __call__(self, attrs):
        student = attrs['student']
        time = attrs['time']
        date = attrs['date']

        self.queryset = self.queryset.filter(date=date).values_list('time')
        times = [item[0] for item in self.queryset]

        for t1 in times:
            t2 = datetime.time(t1.hour+1, t1.minute, t1.second)
            if t1 <= time < t2:
                raise ValidationError(self.message.format(t1))

        if student == '':
            raise ValidationError(_("Please, select a student"))

    def __repr__(self):
        return '<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        )


class UserValidator():
    """
    1. checking the overlap of lessons on each other - for all
    (lesson duration = 1 hour)
    2. check for too early and late lessons by day -  for users only
    3. checking for too early and late lessons by the hour - for users only
    4. checking cost of too early and late lessons by the hour - for users only
    5. checking the lead time - for users only
    (you can not add a lesson earlier than 6 hours)
    6. checking for cost limits (700<=salary) - for users only
    7. check of lesson cost when numbers lesson todate is big - for users only
    """

    def __init__(self, queryset):
        self.queryset = queryset

    def __call__(self, attrs):
        salary = attrs['salary']
        time = attrs['time']
        date = attrs['date']
        dt_now = datetime.datetime.now()

        if salary < C_salary_common:
            raise ValidationError(
                _('The minimum cost of a lesson is {}').format(C_salary_common)
            )
        elif salary > C_salary_max:
            raise ValidationError(
                _('Perfaps you made a mistake in the cost')
            )

        if date < dt_now.date():
            raise ValidationError(_("The date {} has already arrived").format(
                date))
        elif date > (dt_now + C_datedelta).date():
            raise ValidationError(
                _("Please don't book a lesson earlier then {} "
                  "days in advace").format(C_datedelta)
            )

        if datetime.datetime.combine(date, time) < dt_now + C_timedelta:
            raise ValidationError(
                _("Please, sign up for a lesson {} hours before to "
                  "start").format(C_timedelta)
            )

        if time < С_morning_time:
            raise ValidationError(_("The time {} is too early").format(time))
        elif С_morning_time <= time < С_morning_time_markup:
            if salary < C_salary_high:
                raise ValidationError(
                    _("In the morning ({0}-{1} hours) the cost of the lesson"
                      " is {2}").format(
                          С_morning_time, С_morning_time_markup, C_salary_high
                    )
                )
        elif C_evening_time_markup <= time < C_evening_time:
            if salary < C_salary_high:
                raise ValidationError(
                    _("In the evening ({0}-{1}"
                      " hours) the cost of the lesson is {2}").format(
                          C_evening_time_markup, C_evening_time, C_salary_high
                      )
                )
        elif time > C_evening_time:
            raise ValidationError(_("The time {} is too late").format(time))

        self.queryset = self.queryset.filter(date=date).values_list('time')
        times = [item[0] for item in self.queryset]

        for t1 in times:
            t2 = datetime.time(t1.hour+1, t1.minute, t1.second)
            if t1 <= time < t2:
                raise ValidationError(
                    _("Some lesson is already scheduled for "
                      "{} that day").format(t1)
                )

        if len(self.queryset) >= C_lesson_threshold:
            if salary < C_salary_high:
                raise ValidationError(
                    _("Amount of lessons today is greater than or equel "
                      "to {0}. Lesson cost is {1} ₽").format(
                        C_lesson_threshold, C_salary_high
                    )
                )

    def __repr__(self):
        return '<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        )
