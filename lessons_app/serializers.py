from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from django.contrib.auth.models import User

from .models import Lesson, UserDetail, TimeBlock
from .validators import (
    AdminValidator, UserValidator, RegistrationValidator, TimeBlockValidator
)


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
        fields = ('alias', 'skype', 'discord', 'usual_cost', 'high_cost',
                  'phone', 'telegram')


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


class TimeBlockSerializer(serializers.ModelSerializer):
    """ Getting timeblock list """

    class Meta:
        model = TimeBlock
        fields = ('date', 'start_time', 'end_time')


class TimeBlockAdminSerializer(serializers.ModelSerializer):
    """ Admin viewset of Timeblock (admin only) """

    class Meta:
        model = TimeBlock
        fields = ('id', 'date', 'start_time', 'end_time')
        validators = [
            TimeBlockValidator(queryset=model.objects.all())
        ]


class StudentAdminSerializer(serializers.Serializer):
    """ Admin viewset of students (admin only) """

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)
    first_name = serializers.CharField()
    alias = serializers.CharField(source='details.alias')
    usual_cost = serializers.IntegerField(source='details.usual_cost')
    high_cost = serializers.IntegerField(source='details.high_cost')
    telegram = serializers.CharField(source='details.telegram')
    phone = serializers.CharField(source='details.phone')
    discord = serializers.CharField(source='details.discord')
    skype = serializers.CharField(source='details.skype')
    last_login = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField()

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if isinstance(value, dict):
                # instead instance.details (foreign key)
                field = getattr(instance, attr)
                for attr, value in value.items():
                    setattr(field, attr, value)
                field.save()
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance
