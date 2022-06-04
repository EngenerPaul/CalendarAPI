from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from lessons_app.models import UserDetail


class ModelsTestCase(TestCase):
    """ Testing UserDetail model works """
    user_creds = {
        'username': 'test_username',
        'password': 'test_password'
    }

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(**cls.user_creds)
        test_user_details = UserDetail()
        test_user_details.user = test_user
        test_user_details.save()

    def test_url(self):
        """ Url is correct """
        user = User.objects.get(**self.user_creds)
        path = reverse('student_detail_AP_url', kwargs={'pk': user.pk})
        url = user.details.get_absolute_url()
        self.assertEqual(path, url)
