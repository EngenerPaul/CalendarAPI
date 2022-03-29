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
from django.contrib.auth.hashers import make_password

from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from .models import Lesson
from .forms import RegisterUserForm, AuthUserForm, AddLessonForm
from .serializer import UserSerializer, LessonSerializer,\
                        LessonAdminSerializer,\
                        RegistrationSerializer, DelUserSerializer


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


#################################################################
#                            DRF API                            #
#################################################################

class RegistrationAPI(CreateAPIView):
    """ Registration new users """

    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class DeleteUserAPI(DestroyAPIView):
    """ Delete user """

    queryset = User.objects.all()
    serializer_class = DelUserSerializer
    permission_classes = [IsAdminUser]


class UsersAPI(ListAPIView):
    """ Gets user list """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class RelevantLessonsAPI(ListAPIView):
    """ Gets relevant lesson list """

    queryset = Lesson.objects.filter(date__gte=date.today())
    serializer_class = LessonSerializer
    permission_classes = [AllowAny]


class LessonsViewSet(viewsets.ModelViewSet):
    """ ViewSet of own relevant lessons for authenticated user.
    Request type: GET, POST, PUT, PATCH, DELETE """

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        queryset = Lesson.objects.filter(
            student=request.user,
            date__gte=date.today()
        )
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(request, serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, request, serializer):
        serializer.save(student_id=request.user.pk)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset(self.request))
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class LessonsAdminViewSet(viewsets.ModelViewSet):
    """ ViewSet of all lessons """

    queryset = Lesson.objects.all()
    serializer_class = LessonAdminSerializer
    permission_classes = [IsAdminUser]


class RelevantLessonsAdminViewSet(viewsets.ModelViewSet):
    """ ViewSet of all relevant lessons """

    queryset = Lesson.objects.filter(date__gte=date.today())
    serializer_class = LessonAdminSerializer
    permission_classes = [IsAdminUser]
