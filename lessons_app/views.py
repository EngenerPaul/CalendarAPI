from datetime import date

from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, View, \
                                 DeleteView, TemplateView, UpdateView
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

from .models import Lesson
from .forms import RegisterUserForm, AuthUserForm, AddLessonForm


class LessonView(ListView):

    model = Lesson
    template_name = 'lessons_app/index.html'
    context_object_name = 'lessons'

    def get_queryset(self):
        all_lessons = self.model.objects.filter(date__gte=date.today())
        lessons = {}
        for item in all_lessons:
            if item.date in lessons:
                lessons[item.date].append(item)
            else:
                lessons[item.date] = [item]
        return lessons


class LessonByUser(LoginRequiredMixin, ListView):

    model = Lesson
    template_name = 'lessons_app/lessons_by_student.html'
    context_object_name = 'lessons'
    login_url = 'login_url'

    def get_queryset(self):
        lessons = self.model.objects.filter(
            date__gte=date.today(),
            student_id=self.request.user.id
        )
        return lessons


class CustomLoginView(LoginView):
    """Authentication"""

    template_name = "lessons_app/login.html"
    form_class = AuthUserForm
    success_url = reverse_lazy('home_url')

    # because success_url variable does't work
    def get_success_url(self):
        return self.success_url


class CustomRegistration(CreateView):
    """Registration"""

    model = User
    template_name = 'lessons_app/registration.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('home_url')

    def form_valid(self, form):
        """the method is overridden added auto-authentication"""

        form_valid = super().form_valid(form)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        auth_user = authenticate(username=username, password=password)
        login(self.request, auth_user)
        return form_valid


class CustomLogOut(LogoutView):
    """LogOut"""

    next_page = reverse_lazy('home_url')


# class Profile(LoginRequiredMixin, TemplateView):
#     """User profile"""

#     model = User
#     template_name = 'lessons_app/profile.html'
#     context_object_name = 'user'

#     def get_queryset(self):
#         queryset = User.objects.get(pk=self.request.user.pk)
#         return queryset


class AddLessonView(LoginRequiredMixin, CreateView):
    model = Lesson
    template_name = 'lessons_app/add_lesson.html'
    form_class = AddLessonForm
    success_url = 'home_url'
    login_url = 'login_url'

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        self.object.student_id = self.request.user.pk
        self.object.save()
        return HttpResponseRedirect(reverse_lazy(self.success_url))
