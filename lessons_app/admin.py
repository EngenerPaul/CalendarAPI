from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import Lesson, UserDetail


class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'time', 'student', 'theme', 'salary', )
    list_display_links = ('id', )
    ordering = ('-date', 'time', )
    list_per_page = 50


class InlineAdmin(admin.TabularInline):
    list_display = ('phone',)
    model = UserDetail


class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'first_name', )
    list_display_links = ('id', 'username', 'first_name')
    ordering = ('username', )
    list_per_page = 50
    list_select_related = ('details',)
    inlines = [InlineAdmin]


class CustomUserDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'user', 'phone', 'telegram', 'whatsapp')
    list_display_links = ('id', )
    ordering = ('user', )
    list_per_page = 50


admin.site.register(Lesson, LessonAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserDetail, CustomUserDetailAdmin)
