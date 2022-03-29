from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from .models import Lesson


class RegistrationSerializer(serializers.ModelSerializer):
    """ Registraion new user """

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'password')

    def save(self, **kwargs):
        assert hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        # Guard against incorrect use of `serializer.save(commit=False)`
        assert 'commit' not in kwargs, (
            "'commit' is not a valid keyword argument to the 'save()' method. "
            "If you need to access data before committing to the database then"
            "inspect 'serializer.validated_data' instead. "
            "You can also pass additional keyword arguments to 'save()' if you"
            "need to set extra attributes on the saved model instance. "
            "For example: 'serializer.save(owner=request.user)'.'"
        )

        assert not hasattr(self, '_data'), (
            "You cannot call `.save()` after accessing `serializer.data`."
            "If you need to access data before committing to the database then"
            "inspect 'serializer.validated_data' instead. "
        )

        validated_data = {**self.validated_data, **kwargs}
        validated_data['password'] = make_password(validated_data['password'])

        if self.instance is not None:
            self.instance = self.update(self.instance, validated_data)
            assert self.instance is not None, (
                '`update()` did not return an object instance.'
            )
        else:
            self.instance = self.create(validated_data)
            assert self.instance is not None, (
                '`create()` did not return an object instance.'
            )

        return self.instance


class DelUserSerializer(serializers.ModelSerializer):
    """ Deletion user """

    class Meta:
        modal = User
        fields = ('username')


class UserSerializer(serializers.ModelSerializer):
    """ Get User info """

    id = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'is_staff')


class LessonSerializer(serializers.ModelSerializer):
    """ ViewSet of lesson """

    student = PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'student', 'theme', 'salary', 'time', 'date')


class LessonAdminSerializer(serializers.ModelSerializer):
    """ Admin viewset of lesson """

    class Meta:
        model = Lesson
        fields = ('id', 'student', 'theme', 'salary', 'time', 'date')
