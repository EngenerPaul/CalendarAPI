from datetime import date, time, timedelta

from django.test.testcases import TestCase
from django.test.client import Client
from django.contrib.auth.models import User

from lessons_app.models import Lesson, UserDetail, TimeBlock
from CalendarApi.constraints import C_salary_common


class TestAnonymousAbilities(TestCase):
    """ Testing all anonymous user abilities """

    @classmethod
    def setUpTestData(cls):
        user_credentials = {
            'username': 'user1',
            'password': 'pass1'
        }
        user = User.objects.create_user(**user_credentials)
        UserDetail.objects.create(user=user)
        lesson = {
            'student_id': user.pk,
            'date': date.today(),
            'time': time(hour=15, minute=0, second=0),
            'salary': C_salary_common
        }
        Lesson.objects.create(**lesson)
        timeblock = {
            'date': date.today() + timedelta(days=2),
            'start_time': time(hour=12, minute=0, second=0),
            'end_time': time(hour=18, minute=0, second=0)
        }
        TimeBlock.objects.create(**timeblock)

    def test_registration(self):
        form_data = {
            'username': 'new_user',
            'password': 'new_pass',
            'first_name': 'new_name',
            'phone': '',
            'telegram': '@telegram'
        }
        response = self.client.post(
            path='/register',
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')
        self.assertTrue(response.context['user'].is_active)

    def test_of_getting_all_lessons(self):
        response = self.client.get('/')
        objects = []
        for values in response.context_data.get('lessons').values():
            objects.extend(values)
        self.assertTrue(objects)


class TestUserAbilities(TestCase):
    """ Testing all user abilities """

    user_credentials = {
        'username': 'test_user',
        'password': 'test_pass'
    }

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(**TestUserAbilities.user_credentials)
        UserDetail.objects.create(user=user)

        other_user = User.objects.create_user({
            'username': 'other_user',
            'password': 'other_pass'
        })
        UserDetail.objects.create(user=other_user)

        lesson = {
            'student_id': user.pk,
            'date': date.today(),
            'time': time(hour=15, minute=0, second=0),
            'salary': C_salary_common
        }
        Lesson.objects.create(**lesson)
        last_lesson = {
            'student_id': user.pk,
            'date': date.today() - timedelta(days=2),
            'time': time(hour=15, minute=0, second=0),
            'salary': C_salary_common
        }
        Lesson.objects.create(**last_lesson)
        other_user_lesson = {
            'student_id': other_user.pk,
            'date': date.today() + timedelta(days=2),
            'time': time(hour=15, minute=0, second=0),
            'salary': C_salary_common
        }
        Lesson.objects.create(**other_user_lesson)

        timeblock = {
            'date': date.today() + timedelta(days=2),
            'start_time': time(hour=12, minute=0, second=0),
            'end_time': time(hour=18, minute=0, second=0)
        }
        TimeBlock.objects.create(**timeblock)

    def setUp(self):
        self.client.login(**self.user_credentials)

    def test_login(self):
        response = Client().post(
            path='/login',
            data=self.user_credentials,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')
        self.assertTrue(response.context['user'].is_active)

    def test_lesson_creation(self):
        lessons = Lesson.objects.all().count()
        response = self.client.get(
            path='/add-lesson'
        )
        form_date = {
            'time': 12,
            'date': (date.today() + timedelta(days=1)).strftime(r'%Y-%m-%d')
        }
        response = self.client.post(
            path='/add-lesson',
            data=form_date,
            follow=True
        )
        self.assertTrue(Lesson.objects.all().count() > lessons)
        self.assertRedirects(response, '/')
        self.assertEqual(response.status_code, 200)

    def test_own_lesson_review(self):
        response = self.client.get('/my-lessons')
        user_lessons = Lesson.objects.filter(
            date__gte=date.today(),
            student_id=response.context['user'].id
        )
        self.assertQuerysetEqual(response.context['lessons'], user_lessons)
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        response = self.client.post(
            '/logout',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')
        self.assertTrue(response.context['user'].is_anonymous)


class TestAdminAbilities(TestCase):
    """ Testing all admin (superuser) abilities """

    admin_credentials = {
        'username': 'admin',
        'password': 'admin'
    }
    other_user_creds = {
        'username': 'other_user',
        'password': 'Other_pass'
    }

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            **TestAdminAbilities.admin_credentials,
            is_staff=True,
            is_superuser=True
        )
        UserDetail.objects.create(user=user)

        other_user = User.objects.create_user(
            **TestAdminAbilities.other_user_creds)
        UserDetail.objects.create(user=other_user)

    def setUp(self):
        self.client.login(**self.admin_credentials)

    def test_login(self):
        client = Client()
        response = client.post(
            path='/login',
            data=self.admin_credentials,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')
        self.assertTrue(response.context['user'].is_superuser)

    def test_lesson_creation(self):
        student = User.objects.get(username=self.other_user_creds['username'])
        form_data = {
            'student': student.id,
            'time': 18,
            'date': date.today() + timedelta(days=2)
        }
        response = self.client.post(
            path='/admin-panel/add-lesson',
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')
        self.assertTrue(Lesson.objects.filter(student=student))

    def test_timeblock_creation(self):
        timeBlock_amount_before = len(TimeBlock.objects.all())
        form_data = {
            'date': date.today() + timedelta(days=3),
            'start_time': 13,
            'end_time': 18
        }
        response = self.client.post(
            path='/admin-panel/block-time',
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/admin-panel/block-time')
        self.assertTrue(timeBlock_amount_before < len(TimeBlock.objects.all()))

    def test_get_student_list(self):
        response = self.client.get('/admin-panel/students')
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['students'],
            User.objects.filter(is_staff=False)
        )

    def test_get_student_detail(self):
        student = User.objects.get(username=self.other_user_creds['username'])
        response = self.client.get(f'/admin-panel/students/{student.id}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user_details'])

    def test_student_detail_change(self):
        student = User.objects.get(username=self.other_user_creds['username'])
        new_first_name = 'any new name'
        form_data = {
            'pk': student.id,
            'username': student.username,
            'first_name': new_first_name,
            'alias': student.details.alias or '',
            'usual_cost': student.details.usual_cost,
            'high_cost': student.details.high_cost,
            'phone': student.details.phone or '',
            'telegram': student.details.telegram or '',
            'discord': student.details.discord or '',
            'skype': student.details.skype or '',
            'last_login': student.last_login or '',
            'is_active': student.is_active
        }
        response = self.client.post(
            path=f'/admin-panel/students/{student.id}',
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, f'/admin-panel/students/{student.id}')
        self.assertEqual(User.objects.get(id=student.id).first_name,
                         new_first_name)
