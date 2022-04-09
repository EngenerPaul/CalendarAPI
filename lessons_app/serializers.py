from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from django.contrib.auth.models import User

from .models import Lesson, UserDetail
from .validators import AdminValidator, UserValidator, RegistrationValidator


class RegistrationSerializer(serializers.Serializer):
    """ Registraion new user (allow any) """

    username = serializers.CharField()
    first_name = serializers.CharField()
    password = serializers.CharField()
    phone = serializers.CharField()
    telegram = serializers.CharField()

    class Meta:
        validators = [
            RegistrationValidator()
        ]


class DelUserSerializer(serializers.ModelSerializer):
    """ Deletion user (admin only) """

    class Meta:
        modal = User
        fields = ('username')


class UserDetailSerializer(serializers.ModelSerializer):
    """ Nested relationships for UserSerializer (details) """

    class Meta:
        model = UserDetail
        fields = ('phone', 'telegram')


class UserSerializer(serializers.ModelSerializer):
    """ Get User info (admin only) """

    id = serializers.StringRelatedField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField()
    password = serializers.CharField(read_only=True)
    details = UserDetailSerializer()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'first_name', 'is_staff', 'details',
            )


class LessonSerializer(serializers.ModelSerializer):
    """ ViewSet of lesson (allow any (GET) or Authorized only (OTHER)) """

    student = PrimaryKeyRelatedField(read_only=True)
    salary = serializers.IntegerField(read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'student', 'salary', 'time', 'date')
        validators = [
            UserValidator(queryset=Lesson.objects.all())
        ]


class LessonAdminSerializer(serializers.ModelSerializer):
    """ Admin viewset of lesson (admin only) """

    class Meta:
        model = Lesson
        fields = ('id', 'student', 'salary', 'time', 'date')
        validators = [
            AdminValidator(queryset=Lesson.objects.all())
        ]
