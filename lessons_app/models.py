from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.translation import gettext as _

from CalendarApi.constraints import (
    C_salary_common, C_salary_high
)


class Lesson(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    salary = models.IntegerField()
    time = models.TimeField()
    date = models.DateField()

    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        ordering = ('date', 'time')

    def __str__(self):
        return _('The Lesson class: id = {}').format(self.pk)

    def get_absolute_url(self):
        return reverse('add_lesson_url', kwargs={'pk': self.pk})


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='details')
    phone = models.CharField(max_length=11, blank=True, null=True)
    telegram = models.CharField(max_length=30, blank=True, null=True)
    skype = models.CharField(max_length=30, blank=True, null=True)
    discord = models.CharField(max_length=30, blank=True, null=True)
    alias = models.CharField(max_length=50, blank=True, null=True)
    usual_cost = models.IntegerField(blank=True, null=True,
                                     default=C_salary_common)
    high_cost = models.IntegerField(blank=True, null=True,
                                    default=C_salary_high)

    class Meta:
        verbose_name = _('Details')
        verbose_name_plural = _('Details')

    def __str__(self):
        return _('The UserDetail class: id = {}').format(self.user)


class TimeBlock(models.Model):
    """ Time blocking model in admin panel (AP) """

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name = _('TimeBlock')
        verbose_name_plural = _('Timeblocks')
        ordering = ('date', 'start_time')
