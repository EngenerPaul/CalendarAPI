from unicodedata import name
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CustomRegistration, CustomLogOut, CustomLoginView,\
                   AddLessonView, LessonView, LessonByUser,\
                   UsersAPI, RegistrationAPI, RelevantLessonsAPI,\
                   LessonsViewSet, LessonsAdminViewSet,\
                   RelevantLessonsAdminViewSet, DeleteUserAPI

router = DefaultRouter()
router.register('api/set-my-lessons', LessonsViewSet,
                basename='my_lessons')
router.register('api/all-lessons', LessonsAdminViewSet)
router.register('api/all-relevant-lessons', RelevantLessonsAdminViewSet)

urlpatterns = [
    path('', LessonView.as_view(), name='home_url'),
    path('my_lesson', LessonByUser.as_view(), name='lesson_by_student_url'),
    path('register', CustomRegistration.as_view(), name='registration_url'),
    path('logout', CustomLogOut.as_view(), name='logout_url'),
    path('login', CustomLoginView.as_view(), name='login_url'),
    path('add_lesson', AddLessonView.as_view(), name='add_lesson_url'),

    # API
    path('api/registration', RegistrationAPI.as_view()),
    path('api/get-users', UsersAPI.as_view()),
    path('api/get-relevant-lessons', RelevantLessonsAPI.as_view()),
    path('api/delete-user/<int:pk>/', DeleteUserAPI.as_view()),
]

urlpatterns += router.urls
