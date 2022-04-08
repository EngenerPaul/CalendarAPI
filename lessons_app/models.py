from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.translation import gettext as _


class Lesson(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    theme = models.CharField(
        max_length=100,
        default=_('Consultation'),
        blank=True,
        null=True
    )
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

    class Meta:
        verbose_name = _('Details')
        verbose_name_plural = _('Details')

    def __str__(self):
        return _('The UserDetail class: id = {}').format(self.user)
