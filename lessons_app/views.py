from copy import deepcopy
from datetime import date, timedelta, datetime

from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, CreateView, DeleteView, View, TemplateView, DetailView
)
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.hashers import make_password

from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, CreateAPIView, DestroyAPIView, get_object_or_404
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Lesson, UserDetail, TimeBlock
from .forms import (
    RegisterUserForm, AuthUserForm, AddLessonForm, AddLessonAdminForm,
    TimeBlockerAPForm, StudentUpdateForm
)
from .serializers import (
    UserSerializer, LessonSerializer, LessonAdminSerializer,
    RegistrationSerializer, DelUserSerializer,
    TimeBlockSerializer, TimeBlockAdminSerializer, StudentAdminSerializer
)
from CalendarApi.constraints import (
    С_morning_time, С_morning_time_markup, C_evening_time_markup,
    C_evening_time, C_salary_common, C_salary_high, C_lesson_threshold,
    C_timedelta, C_datedelta
)


def get_weekdays():
    date_choices = []
    weekdays = {
        'Monday': _('Monday'),
        'Tuesday': _('Tuesday'),
        'Wednesday': _('Wednesday'),
        'Thursday': _('Thursday'),
        'Friday': _('Friday'),
        'Saturday': _('Saturday'),
        'Sunday': _('Sunday'),
    }
    for i in range(C_datedelta.days+1):
        if i == 0:
            day = date.today() + timedelta(days=i)
            day_title = (f"{_('Today')}, "
                         f"{datetime.strftime(day, r'%d-%m')}")
            date_choices.append((day, day_title))
            continue
        day = date.today() + timedelta(days=i)
        day_title = (f"{weekdays[day.strftime('%A')]}, "
                     f"{datetime.strftime(day, r'%d-%m')}")
        date_choices.append((day, day_title))

    return date_choices


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

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect('home_url')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        lessons = self.model.objects.filter(
            date__gte=date.today(),
            student_id=self.request.user.id
        )
        return lessons

    def post(self, request):
        if request.POST.get('new_password'):
            return self.change_password(request)
        return redirect('lesson_by_student_url')

    def change_password(self, request):
        new_pass = request.POST.get("new_password")
        student = request.user
        student.password = make_password(new_pass)
        student.save()

        auth_user = authenticate(
            username=student.username,
            password=student.password
        )
        login(self.request, auth_user)
        messages.success(
            request,
            _("Your password changed successfully. Login: {}, "
              "new password: {}").format(
                  student.username, new_pass)
        )
        return redirect('lesson_by_student_url')


class CustomLoginView(LoginView):
    """Authentication"""

    template_name = "lessons_app/login.html"
    form_class = AuthUserForm
    success_url = reverse_lazy('home_url')

    # because success_url variable does't work
    def get_success_url(self):
        return self.success_url

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home_url')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            messages.error(
                request,
                _('You can write to me on telegram @spacepython if you forgot '
                  'your password')
            )
            return self.form_invalid(form)


class CustomRegistrationView(CreateView):
    """Registration"""

    model = User
    template_name = 'lessons_app/registration.html'
    success_url = reverse_lazy('home_url')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home_url')
        return super().dispatch(request, *args, **kwargs)

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

        user = self.model()
        userdetail = UserDetail()

        user.username = form.cleaned_data['username']
        user.password = make_password(form.cleaned_data['password'])
        user.first_name = form.cleaned_data['first_name']

        userdetail.user = user
        userdetail.phone = form.cleaned_data['phone']
        userdetail.telegram = form.cleaned_data['telegram']

        user.save()
        userdetail.save()
        messages.success(
            request,
            _("Registration completed. Please write down your "
              "username and password so you don't forget")
        )

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

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect('add_lesson_AP_url')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name,
                      self.get_context_data(request))

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

        cost_messages = []
        cost_messages.append(_(
                "The cost of a usual lesson is {} ₽"
            ).format(usual_cost)
        )
        cost_messages.append(_(
                "The cost of a lesson in the early morning to {} is {} ₽."
            ).format(С_morning_time_markup.strftime(r'%H:%M'), high_cost)
        )
        cost_messages.append(_(
                "The cost of a lesson in the late evening to {} is {} ₽."
            ).format(C_evening_time_markup.strftime(r'%H:%M'), high_cost)
        )
        cost_messages.append(_(
                "The cost of a lesson when day is full ({} lessons per day) "
                "is {} ₽."
            ).format(C_lesson_threshold, high_cost)
        )
        context['cost_messages'] = cost_messages

        context['C_timedelta'] = C_timedelta.seconds // 3600

        form = self.get_form(self.form_class)
        context['form'] = form
        return context

    def get_form(self, form_class):
        form = super().get_form(form_class)
        date_choices = get_weekdays()
        form.fields['date'].widget.choices = date_choices
        return form

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
        context['C_timedelta'] = C_timedelta.seconds // 3600
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
        context['С_morning_time'] = С_morning_time
        context['С_morning_time_markup'] = С_morning_time_markup
        context['C_evening_time_markup'] = C_evening_time_markup
        context['C_evening_time'] = C_evening_time
        context['C_salary_common'] = C_salary_common
        context['C_salary_high'] = C_salary_high
        C_timedelta_hours = str(C_timedelta.seconds // 3600)
        C_timedelta_minutes = str(C_timedelta.seconds % 60).ljust(2, '0')
        context['C_timedelta'] = C_timedelta_hours + ':' + C_timedelta_minutes
        context['C_datedelta'] = C_datedelta.days
        context['C_lesson_threshold'] = C_lesson_threshold - 1
        return context


class AddLessonAP(AdminAccessMixin, CreateView):
    """ Create lesson for students by admin """

    model = Lesson
    template_name = 'lessons_app/management/add_lesson_admin.html'
    form_class = AddLessonAdminForm
    success_url = 'home_url'
    title = _('Add lesson by admin')

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = {}

        cost_messages = []
        cost_messages.append(_(
                "The cost of a usual lesson is {} ₽"
            ).format(C_salary_common)
        )
        cost_messages.append(_(
                "The cost of a lesson in the early morning to {} is {} ₽."
            ).format(С_morning_time_markup.strftime(r'%H:%M'), C_salary_high)
        )
        cost_messages.append(_(
                "The cost of a lesson in the late evening to {} is {} ₽."
            ).format(C_evening_time_markup.strftime(r'%H:%M'), C_salary_high)
        )
        cost_messages.append(_(
                "The cost of a lesson when day is full ({} lessons per day) "
                "is {} ₽."
            ).format(C_lesson_threshold, C_salary_high)
        )
        context['cost_messages'] = cost_messages

        context['menu'] = admin_panel
        context['title'] = self.title

        form = self.get_form(self.form_class)
        context['form'] = form
        return context

    def get_form(self, form_class):
        form = super().get_form(form_class)

        student_choices = []
        students = User.objects.filter(
            is_staff=False, is_active=True
        ).select_related('details').order_by('details__alias')
        for student in students:
            if student.details.alias:
                student_choices.append((
                    student.id,
                    f"{student.details.alias} ({student.first_name})"
                ))
            else:
                student_choices.append((
                    student.id,
                    f"{student.first_name}"
                ))
        form.fields['student'].widget.choices = student_choices

        date_choices = get_weekdays()
        form.fields['date'].widget.choices = date_choices

        return form

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
        lesson.student_id = form.cleaned_data['student']

        is_morning = С_morning_time <= time < С_morning_time_markup
        is_evening = C_evening_time_markup < time <= C_evening_time
        is_over = len(Lesson.objects.filter(date=date)
                      ) >= C_lesson_threshold - 1
        # value existence check can be disabled in the future
        user_detail = UserDetail.objects.get(
            user_id=form.cleaned_data['student']
        )
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

        lesson.time = time
        lesson.date = date

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


class TimeBlockerAP(AdminAccessMixin, FormMixin, ListView):
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
        form = self.get_form()
        context['form'] = form
        return context

    def get_form(self):
        form = super().get_form()
        date_choices = get_weekdays()
        form.fields['date'].widget.choices = date_choices
        return form

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
    """ Student list in the admin panel """

    model = User
    context_object_name = 'students'
    title = _('Students')
    template_name = 'lessons_app/management/students_info.html'

    def get_queryset(self):
        return self.model.objects.filter(
            is_staff=False
        ).select_related('details').order_by('details__alias', 'first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = admin_panel
        context['title'] = self.title
        return context


class StudentDetailAP(AdminAccessMixin, DetailView):
    """ User details in the admin panel """

    model = User
    template_name = 'lessons_app/management/student_info.html'
    context_object_name = 'user_details'
    form_class = StudentUpdateForm

    def post(self, request, *args, **kwargs):
        if request.POST.get('new_password'):
            return self.change_password(request)
        if request.POST.get('delete lesson'):
            return self.delete_lesson(request)
        form = self.form_class(request.POST)
        if form.is_valid():
            return self.form_valid(request, form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = admin_panel

        user_pk = self.kwargs.get(self.pk_url_kwarg)
        user = self.model.objects.select_related('details').get(pk=user_pk)
        context['form'] = self.form_class(initial={
            'pk': user.pk,
            'username': user.username,
            'first_name': user.first_name,
            'alias': user.details.alias,
            'usual_cost': user.details.usual_cost,
            'high_cost': user.details.high_cost,
            'phone': user.details.phone,
            'telegram': user.details.telegram,
            'discord': user.details.discord,
            'skype': user.details.skype,
            'last_login': user.last_login,
            'is_active': user.is_active
            })

        context['student_lessons'] = Lesson.objects.filter(
            student_id=user_pk,
            date__gte=date.today()
        )
        context['title'] = StudentsAP.title
        return context

    def form_valid(self, request, form):
        pk = form.cleaned_data['pk']
        user = self.model.objects.select_related('details').get(pk=pk)

        user.first_name = form.cleaned_data['first_name']
        user.details.alias = form.cleaned_data['alias']
        user.details.usual_cost = form.cleaned_data['usual_cost']
        user.details.high_cost = form.cleaned_data['high_cost']
        user.details.phone = form.cleaned_data['phone']
        user.details.telegram = form.cleaned_data['telegram']
        user.details.discord = form.cleaned_data['discord']
        user.details.skype = form.cleaned_data['skype']
        user.is_active = form.cleaned_data['is_active']

        user.details.save()
        user.save()
        messages.success(request, _('User information changed successfully'))
        return redirect(reverse_lazy('student_detail_AP_url',
                                     kwargs={'pk': form.cleaned_data['pk']}))

    def delete_lesson(self, request):
        lesson_id = request.POST.get('delete lesson')
        lesson = Lesson.objects.get(pk=lesson_id)
        lesson.delete()
        messages.success(
            request,
            _("Lesson deleted successfully")
        )
        url_pk = self.kwargs.get(self.pk_url_kwarg)
        return redirect(reverse_lazy('student_detail_AP_url',
                                     kwargs={'pk': url_pk}))

    def change_password(self, request):
        new_pass = request.POST.get("new_password")
        url_pk = self.kwargs.get(self.pk_url_kwarg)
        student = User.objects.get(pk=url_pk)
        student.password = make_password(new_pass)
        student.save()
        messages.success(
            request,
            _("Student password changed successfully. Username: {}, "
              "new password: {}").format(
                  student.username, new_pass)
        )
        return redirect(reverse_lazy('student_detail_AP_url',
                                     kwargs={'pk': url_pk}))


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
        return Response(serializer.data, status=status.HTTP_200_OK)


class RelevantLessonsAPI(ListAPIView):
    """ Gets relevant lesson list """

    serializer_class = LessonSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Lesson.objects.filter(
            date__gte=date.today()
        )
        return queryset


class LessonsViewSet(viewsets.ModelViewSet):
    """ ViewSet of own relevant lessons for authenticated user.
    Request type: GET, POST, PUT, PATCH, DELETE """

    queryset = Lesson.objects.filter(date__gte=date.today())
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        time = serializer.validated_data['time']
        date = serializer.validated_data['date']
        is_morning = С_morning_time <= time < С_morning_time_markup
        is_evening = C_evening_time_markup < time <= C_evening_time
        is_over = len(Lesson.objects.filter(date=date)
                      ) >= C_lesson_threshold - 1
        # value existence check can be disabled in the future
        user_detail = UserDetail.objects.get(user_id=self.request.user.id)
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

        serializer.save(student_id=self.request.user.pk, salary=salary)


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


class TimeBlockAdminAPI(viewsets.ModelViewSet):
    """ ViewSet of all future Timeblocks for admin """

    queryset = TimeBlock.objects.filter(date__gte=date.today())
    serializer_class = TimeBlockAdminSerializer
    permission_classes = [IsAdminUser]


class StudentAdminAPI(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """ ViewSet to receive and change students for admin """

    queryset = User.objects.select_related('details').filter(is_staff=False)
    serializer_class = StudentAdminSerializer
    permission_classes = [IsAdminUser]
