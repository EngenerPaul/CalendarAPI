from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Lesson(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    theme = models.CharField(
        max_length=100,
        default='Consultation',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    salary = models.IntegerField()
    time = models.TimeField()
    date = models.DateField()

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ('date', 'time')

    def __str__(self):
        return f'The Lesson class: id = {self.pk}'

    def get_absolute_url(self):
        return reverse('add_lesson_url', kwargs={'pk': self.pk})
