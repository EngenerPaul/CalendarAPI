from django import template

from lessons_app.models import Lesson, TimeBlock


register = template.Library()


@register.simple_tag
def is_TimeBlock(obj):
    return isinstance(obj, TimeBlock)
