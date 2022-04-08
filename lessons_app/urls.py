from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CustomRegistrationView, CustomLogOutView, CustomLoginView, AddLessonView,
    DeleteLessonView, LessonView, LessonByUserView, AddLessonAdminView,
    InfoView,
    UsersAPI, RegistrationAPI, RelevantLessonsAPI, LessonsViewSet,
    LessonsAdminViewSet, RelevantLessonsAdminViewSet, DeleteUserAPI,
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
    path('add-lesson-admin', AddLessonAdminView.as_view(),
         name='add_lesson_admin_url'),
    path('delete-lesson/<int:pk>/', DeleteLessonView.as_view(),
         name='del_lesson_url'),
    path('info', InfoView.as_view(), name='info_url'),

    # API
    path('api/registration', RegistrationAPI.as_view()),
    path('api/get-users', UsersAPI.as_view()),
    path('api/get-relevant-lessons', RelevantLessonsAPI.as_view()),
    path('api/delete-user/<int:pk>/', DeleteUserAPI.as_view()),
]

urlpatterns += router.urls
