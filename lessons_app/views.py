from copy import deepcopy
from datetime import date, timedelta, datetime

from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, CreateView, DeleteView, View, TemplateView, UpdateView
)
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.hashers import make_password

from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, CreateAPIView, DestroyAPIView, get_object_or_404
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Lesson, UserDetail, TimeBlock
from .forms import (
    RegisterUserForm, AuthUserForm, AddLessonForm, AddLessonAdminForm,
    TimeBlockerAPForm
)
from .serializers import (
    UserSerializer, LessonSerializer, LessonAdminSerializer,
    RegistrationSerializer, DelUserSerializer,
    TimeBlockSerializer
)
from CalendarApi.constraints import (
    С_morning_time, С_morning_time_markup, C_evening_time_markup,
    C_evening_time, C_salary_common, C_salary_high, C_lesson_threshold,
    C_datedelta
)


class LessonView(ListView):
    """ Get relevant lesson list """

    model = Lesson
    template_name = 'lessons_app/index.html'
    context_object_name = 'lessons'

    def get_queryset(self):
        today = date.today()
        lessons = self.model.objects.filter(
            date__gte=today
        ).select_related(
            'student',
            'student__details'
        )
        lessons = list(lessons)
        blocked_times = TimeBlock.objects.filter(
            date__gte=today,
            date__lte=today + C_datedelta
        )
        blocked_times = list(blocked_times)
        query = {today + timedelta(days=i): [] for i in range(
            C_datedelta.days+1
        )}
        for _ in range(len(lessons) + len(blocked_times)):
            if lessons and blocked_times:
                condition_1 = lessons[0].date < blocked_times[0].date
                condition_2 = (
                    lessons[0].date == blocked_times[0].date and
                    lessons[0].time < blocked_times[0].start_time
                )
                if condition_1 or condition_2:
                    day = lessons[0].date
                    query[day].append(lessons.pop(0))
                else:
                    day = blocked_times[0].date
                    query[day].append(blocked_times.pop(0))
            else:
                exists = lessons or blocked_times
                day = exists[0].date
                query[day].append(exists.pop(0))
        return query


class LessonByUserView(LoginRequiredMixin, ListView):
    """ Get relevant lesson list for every student """

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


class CustomRegistrationView(CreateView):
    """Registration"""

    # model = User
    template_name = 'lessons_app/registration.html'
    success_url = reverse_lazy('home_url')

    def get(self, request, *args, **kwargs):
        form = RegisterUserForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = RegisterUserForm(request.POST)
        if form.is_valid(request, form):
            return self.form_valid(request, form)
        else:
            return redirect('registration_url')

    def form_valid(self, request, form):
        """ Create user and userdetail records and also added
        auto-authentication """

        user = User()
        userdetail = UserDetail()

        user.username = form.cleaned_data['username']
        user.password = make_password(form.cleaned_data['password'])
        user.first_name = form.cleaned_data['first_name']

        userdetail.user = user
        userdetail.phone = form.cleaned_data['phone']
        userdetail.telegram = form.cleaned_data['telegram']

        user.save()
        userdetail.save()
        messages.success(request, _("Registration completed"))

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        auth_user = authenticate(username=username, password=password)
        login(self.request, auth_user)

        return redirect('home_url')


class CustomLogOutView(LogoutView):
    """LogOut"""

    next_page = reverse_lazy('home_url')


class AddLessonView(LoginRequiredMixin, CreateView):
    """ Create a new lesson """

    model = Lesson
    template_name = 'lessons_app/add_lesson.html'
    form_class = AddLessonForm
    success_url = 'home_url'
    login_url = 'login_url'

    def get(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect('add_lesson_AP_url')
        form = self.form_class()
        context = self.get_context_data(request)
        context['form'] = form
        return render(request, self.template_name, context)

    def get_context_data(self, request, **kwargs):
        context = {}
        # value existence check can be disabled in the future
        user_detail = UserDetail.objects.get(user_id=request.user.id)
        if user_detail.usual_cost and user_detail.high_cost:
            usual_cost = user_detail.usual_cost
            high_cost = user_detail.high_cost
        else:
            usual_cost = C_salary_common
            high_cost = C_salary_high

        context['message_1'] = _(
            "The cost of a usual lesson is {} ₽"
        ).format(usual_cost)
        context['message_2'] = _(
            "The cost of a lesson in the early morning to {} is {} ₽."
        ).format(С_morning_time_markup.strftime(r'%H:%M'), high_cost)
        context['message_3'] = _(
            "The cost of a lesson in the late evening to {} is {} ₽."
        ).format(C_evening_time_markup.strftime(r'%H:%M'), high_cost)
        context['message_4'] = _(
            "The cost of a lesson when day is full ({} lessons per day) "
            "is {} ₽."
        ).format(C_lesson_threshold, high_cost)
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid(request, form):
            return self.form_valid(request, form)
        else:
            return redirect('add_lesson_url')

    def form_valid(self, request, form):
        time = str(form.cleaned_data['time']).split(':')[0]
        time = datetime.strptime(time, r"%H").time()
        date = datetime.strptime(
            form.cleaned_data['date'],
            r"%Y-%m-%d"
        ).date()

        lesson = self.model()
        lesson.time = time
        lesson.date = date
        lesson.student_id = request.user.pk

        is_morning = С_morning_time <= time < С_morning_time_markup
        is_evening = C_evening_time_markup < time <= C_evening_time
        is_over = len(Lesson.objects.filter(date=date)
                      ) >= C_lesson_threshold - 1
        # value existence check can be disabled in the future
        user_detail = UserDetail.objects.get(user_id=request.user.id)
        if is_morning or is_evening or is_over:
            if user_detail.high_cost:
                lesson.salary = user_detail.high_cost
            else:
                lesson.salary = C_salary_high
        else:
            if user_detail.usual_cost:
                lesson.salary = user_detail.usual_cost
            else:
                lesson.salary = C_salary_common

        lesson.save()

        messages.success(
            request,
            _("Lesson successfully created. Date: {0}. "
              "Time: {1}. Cost: {2} ₽").format(
                  date.strftime(r'%d-%m-%Y'), time.strftime(r'%H:%M'),
                  lesson.salary
            )
        )
        return HttpResponseRedirect(reverse_lazy(self.success_url))


class DeleteLessonView(LoginRequiredMixin, DeleteView):
    """ Delete lesson by user """

    model = Lesson
    template_name = 'lesson_by_student_url'

    def get_success_url(self, **kwargs):
        return reverse_lazy('lesson_by_student_url')

    def post(self, request, *args, **kwargs):
        # passes the request to form_valid()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(request, form)
        else:
            messages.error(
                request,
                _("Error: the lesson wasn't deleted")
            )
            return self.form_invalid(form)

    def form_valid(self, request, form):
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(
            request,
            _("The lesson successfully deleted")
        )
        return HttpResponseRedirect(success_url)


class InfoView(View):
    """ All information about me """

    def get(self, request, *arg, **kwargs):
        context = self.get_context_data()
        return render(request, 'lessons_app/info.html', context)

    def get_context_data(self, **kwargs):
        context = {}
        context['age'] = self.my_age()
        context['C_salary_common'] = C_salary_common
        context['C_salary_high'] = C_salary_high
        context['С_morning_time_markup'] = С_morning_time_markup.strftime(
            '%H:%M')
        context['C_evening_time_markup'] = C_evening_time_markup.strftime(
            '%H:%M')
        context['C_lesson_threshold'] = C_lesson_threshold
        return context

    def my_age(self):
        """this function shows my age today"""

        today = date.today()
        birthday = date(year=today.year, month=5, day=18)
        birthdate = date(year=1996, month=8, day=23)

        age = today.year - birthdate.year
        if today >= birthday:
            return age
        else:
            return age - 1


#################################################################
#                        ADMIN PANEL (AP)                       #
#################################################################


class AdminAccessMixin:
    """ Admin access only. Other users go to the homepage """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('home_url')
        return super().dispatch(request, *args, **kwargs)


class SettingsAP(AdminAccessMixin, TemplateView):
    title = _('Settings')
    template_name = 'lessons_app/management/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = admin_panel
        context['title'] = self.title
        return context


class AddLessonAP(AdminAccessMixin, CreateView):
    """ Create lesson for students by admin """

    model = Lesson
    template_name = 'lessons_app/management/add_lesson_admin.html'
    form_class = AddLessonAdminForm
    success_url = 'home_url'
    title = _('Add lesson by admin')

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('add_lesson_url')
        form = self.form_class()
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = {}
        context['message_1'] = _(
            "The cost of a usual lesson is {} ₽"
        ).format(C_salary_common)
        context['message_2'] = _(
            "The cost of a lesson in the early morning to {} is {} ₽."
        ).format(С_morning_time_markup.strftime(r'%H:%M'), C_salary_high)
        context['message_3'] = _(
            "The cost of a lesson in the late evening to {} is {} ₽."
        ).format(C_evening_time_markup.strftime(r'%H:%M'), C_salary_high)
        context['message_4'] = _(
            "The cost of a lesson when day is full ({} lessons per day) "
            "is {} ₽."
        ).format(C_lesson_threshold, C_salary_high)
        context['menu'] = admin_panel
        context['title'] = self.title
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid(request, form):
            return self.form_valid(request, form)
        else:
            return redirect('add_lesson_url')

    def form_valid(self, request, form):
        time = str(form.cleaned_data['time']).split(':')[0]
        time = datetime.strptime(time, r"%H").time()
        date = datetime.strptime(
            form.cleaned_data['date'],
            r"%Y-%m-%d"
        ).date()

        lesson = self.model()
        lesson.time = time
        lesson.date = date
        lesson.student_id = form.cleaned_data['student']
        lesson.salary = form.cleaned_data['salary']
        lesson.save()

        messages.success(
            request,
            _("Lesson successfully created. Date: {0}. "
              "Time: {1}. Cost: {2} ₽").format(
                  date.strftime(r'%d-%m-%Y'), time.strftime(r'%H:%M'),
                  lesson.salary
            )
        )
        return HttpResponseRedirect(reverse_lazy(self.success_url))


class TimeBlockerAP(AdminAccessMixin, ListView):
    """ Blocks specified time in the admin panel """

    model = TimeBlock
    context_object_name = 'blocked_times'
    title = _('Time blocker')
    template_name = 'lessons_app/management/time_blocker.html'
    form_class = TimeBlockerAPForm

    def get_queryset(self):
        return self.model.objects.filter(date__gte=date.today())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = admin_panel
        context['title'] = self.title
        form = self.form_class
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('delete block'):
            return self.delete(request)
        form = self.form_class(request.POST)
        if form.is_valid(request):
            return self.form_valid(request, form)
        else:
            return redirect(reverse_lazy('time_blocker_AP_url'))

    def delete(self, request, *args, **kwargs):
        pk = request.POST.get('delete block')
        self.model.objects.get(pk=pk).delete()
        messages.success(
            request,
            _("Block deleted successfully")
        )
        return redirect(reverse_lazy('time_blocker_AP_url'))

    def form_valid(self, request, form):
        date = form.cleaned_data['date']
        start_time = form.cleaned_data['start_time']
        end_time = form.cleaned_data['end_time']
        date = datetime.strptime(date, r"%Y-%m-%d").date()
        start_time = datetime.strptime(str(start_time), r"%H").time()
        end_time = datetime.strptime(str(end_time), r"%H").time()

        blocked_time = self.model()
        blocked_time.date = date
        blocked_time.start_time = start_time
        blocked_time.end_time = end_time
        blocked_time.save()

        messages.success(
            request,
            _("Block created successfully")
        )
        return redirect(reverse_lazy('time_blocker_AP_url'))


class StudentsAP(AdminAccessMixin, ListView):

    model = User
    title = _('Students')
    template_name = 'lessons_app/management/students_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = admin_panel
        context['title'] = self.title
        return context


class LessonsAP(AdminAccessMixin, ListView):

    model = Lesson
    template_name = 'lessons_app/management/lessons_info.html'


class LessonAP(AdminAccessMixin, UpdateView):

    model = Lesson
    template_name = 'lessons_app/management/lesson_info.html'


admin_panel = [
    (SettingsAP.title, 'settingAP_url'),
    (AddLessonAP.title, 'add_lesson_AP_url'),
    (TimeBlockerAP.title, 'time_blocker_AP_url'),
    (StudentsAP.title, 'students_AP_url')
]


#################################################################
#                            DRF API                            #
#################################################################


class RegistrationAPI(CreateAPIView):
    """ Registration new users.
    get_serializer(), get_serializer_class(), get_serializer_context()
    uses from GenericAPIView.
    get_success_headers() uses from CreateModelMixin"""

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User()
        userdetail = UserDetail()

        user.username = serializer.data['username']
        user.password = make_password(serializer.data['password'])
        user.first_name = serializer.data['first_name']

        userdetail.user = user
        userdetail.phone = serializer.data['phone']
        userdetail.telegram = serializer.data['telegram']

        user.save()
        userdetail.save()

        obj = deepcopy(serializer.data)
        obj['id'] = user.id

        headers = self.get_success_headers(serializer.data)
        return Response(
            obj,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class DeleteUserAPI(DestroyAPIView):
    """ Delete user """

    queryset = User.objects.all()
    serializer_class = DelUserSerializer
    permission_classes = [IsAdminUser]


class UsersAPI(ListAPIView):
    """ Gets user list """

    queryset = User.objects.all().order_by('pk').select_related('details')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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
        time = serializer.validated_data['time']
        date = serializer.validated_data['date']
        is_morning = С_morning_time <= time < С_morning_time_markup
        is_evening = C_evening_time_markup < time <= C_evening_time
        is_over = len(Lesson.objects.filter(date=date)
                      ) >= C_lesson_threshold - 1
        # value existence check can be disabled in the future
        user_detail = UserDetail.objects.get(user_id=request.user.id)
        if is_morning or is_evening or is_over:
            if user_detail.high_cost:
                salary = user_detail.high_cost
            else:
                salary = C_salary_high
        else:
            if user_detail.usual_cost:
                salary = user_detail.usual_cost
            else:
                salary = C_salary_common

        serializer.save(student_id=request.user.pk, salary=salary)

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


#################################################################
#                      ADMIN PANEL (AP) API                     #
#################################################################


class TimeBlockAPI(ListAPIView):
    """ Getting block list """

    queryset = TimeBlock.objects.filter(
        date__gte=date.today(),
        date__lte=date.today() + C_datedelta
    )
    serializer_class = TimeBlockSerializer
    permission_classes = [AllowAny]
