from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CustomRegistrationView, CustomLogOutView, CustomLoginView, AddLessonView,
    DeleteLessonView, LessonView, LessonByUserView,
    InfoView,
    SettingsAP, AddLessonAP, TimeBlockerAP, StudentsAP, LessonsAP, LessonAP,
    UsersAPI, RegistrationAPI, RelevantLessonsAPI, LessonsViewSet,
    LessonsAdminViewSet, RelevantLessonsAdminViewSet, DeleteUserAPI,
    TimeBlockAPI,
)

router = DefaultRouter()
router.register('api/set-my-lessons', LessonsViewSet,
                basename='my_lessons')
router.register('api/all-lessons', LessonsAdminViewSet)
router.register('api/all-relevant-lessons', RelevantLessonsAdminViewSet)

urlpatterns = [
    path('', LessonView.as_view(), name='home_url'),
    path('my-lessons', LessonByUserView.as_view(),
         name='lesson_by_student_url'),
    path('register', CustomRegistrationView.as_view(),
         name='registration_url'),
    path('logout', CustomLogOutView.as_view(), name='logout_url'),
    path('login', CustomLoginView.as_view(), name='login_url'),
    path('add-lesson', AddLessonView.as_view(), name='add_lesson_url'),
    path('delete-lesson/<int:pk>/', DeleteLessonView.as_view(),
         name='del_lesson_url'),
    path('info', InfoView.as_view(), name='info_url'),

    # Admin panel
    path('admin-panel/settings', SettingsAP.as_view(),
         name='settingAP_url'),
    path('admin-panel/add-lesson', AddLessonAP.as_view(),
         name='add_lesson_AP_url'),
    path('admin-panel/block-time', TimeBlockerAP.as_view(),
         name='time_blocker_AP_url'),
    path('admin-panel/students', StudentsAP.as_view(),
         name='students_AP_url'),
    path('admin-panel/students/lessons/<int:pk>', LessonsAP.as_view(),
         name='lessons_AP_url'),
    path('admin-panel/students/lessons/lesson/<int:pk>', LessonAP.as_view(),
         name='lesson_AP_url'),

    # API
    path('api/registration', RegistrationAPI.as_view()),
    path('api/get-users', UsersAPI.as_view()),
    path('api/get-relevant-lessons', RelevantLessonsAPI.as_view()),
    path('api/delete-user/<int:pk>/', DeleteUserAPI.as_view()),

    # Admin panel API
    path('api/get-timeblocks', TimeBlockAPI.as_view()),
]

urlpatterns += router.urls
