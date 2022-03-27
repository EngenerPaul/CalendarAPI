from unicodedata import name
from django.urls import path, include

from .views import CustomRegistration, CustomLogOut, CustomLoginView,\
                   AddLessonView, LessonView, LessonByUser


urlpatterns = [
    path('', LessonView.as_view(), name='home_url'),
    path('my_lesson', LessonByUser.as_view(), name='lesson_by_student_url'),
    path('register', CustomRegistration.as_view(), name='registration_url'),
    path('logout', CustomLogOut.as_view(), name='logout_url'),
    path('login', CustomLoginView.as_view(), name='login_url'),
    # path('profile', Profile.as_view(), name='profile_url'),
    path('add_lesson', AddLessonView.as_view(), name='add_lesson_url'),
]
