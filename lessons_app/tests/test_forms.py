from datetime import date, time, timedelta, datetime

from django.test.testcases import TestCase
from django.contrib.auth.models import User

from lessons_app.models import Lesson, UserDetail, TimeBlock
from CalendarApi.constraints import (
    С_morning_time, С_morning_time_markup, C_evening_time_markup,
    C_evening_time, C_salary_common, C_salary_high, C_timedelta,
    C_datedelta, C_lesson_threshold
)


class TestAddLessonForm(TestCase):
    """ Testing validation of the add-lesson form """

    path = '/add-lesson'
    student_creds = {
        'username': 'anyusername',
        'password': 'anypassord'
    }

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(**cls.student_creds)
        UserDetail.objects.create(user=cls.student)

        lesson_form = {
            'student_id': cls.student.pk,
            'date': date.today() + timedelta(days=1),
            'time': time(hour=12, minute=0, second=0),
            'salary': C_salary_common
        }
        Lesson.objects.create(**lesson_form)

        timeblock_form = {
            'date': date.today() + timedelta(days=2),
            'start_time': time(hour=8, minute=0, second=0),
            'end_time': time(hour=23, minute=0, second=0)
        }
        TimeBlock.objects.create(**timeblock_form)

    def setUp(self):
        self.client.login(**self.student_creds)

    def test_lesson_creation(self):
        """ The check of success lesson creation """

        lesson_amount = Lesson.objects.count()
        form_data = {
            'student': self.student.id,
            'time': 18,
            'date': date.today() + timedelta(days=3)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'success')
        self.assertTrue(Lesson.objects.count() > lesson_amount)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')

    def test_lesson_creation_for_taken_time(self):
        """ The check error receiving when lesson time is taken """

        lesson_amount = Lesson.objects.count()
        form_data = {
            'student': self.student.id,
            'time': 12,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
        self.assertTrue(Lesson.objects.count() == lesson_amount)

    def test_lesson_creation_for_blocked_time(self):
        """ The check error receiving when lesson time is blocked """

        lesson_amount = Lesson.objects.count()
        form_data = {
            'student': self.student.id,
            'time': 12,
            'date': date.today() + timedelta(days=2)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
        self.assertTrue(Lesson.objects.count() == lesson_amount)

    def test_lesson_creation_sooner_or_later_time(self):
        """ The check error receiving when lesson time beyond working time """

        lesson_amount = Lesson.objects.count()
        form_data = {
            'student': self.student.id,
            'time': С_morning_time.hour - 1,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
        self.assertTrue(Lesson.objects.count() == lesson_amount)

        form_data = {
            'student': self.student.id,
            'time': С_morning_time.hour,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'success')
        self.assertTrue(Lesson.objects.count() == lesson_amount + 1)

        form_data = {
            'student': self.student.id,
            'time': C_evening_time.hour,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'success')
        self.assertTrue(Lesson.objects.count() == lesson_amount + 2)

        form_data = {
            'student': self.student.id,
            'time': C_evening_time.hour + 1,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
        self.assertTrue(Lesson.objects.count() == lesson_amount + 2)

    def test_test_lesson_creation_sooner_or_later_date(self):
        """ The check error receiving when date beyond constrains date """

        lesson_amount = Lesson.objects.count()
        form_data = {
            'student': self.student.id,
            'time': 12,
            'date': date.today() - timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
        self.assertTrue(Lesson.objects.count() == lesson_amount)

        form_data = {
            'student': self.student.id,
            'time': 12,
            'date': date.today() + timedelta(days=C_datedelta.days)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'success')
        self.assertTrue(Lesson.objects.count() == lesson_amount + 1)

        form_data = {
            'student': self.student.id,
            'time': 12,
            'date': date.today() + timedelta(days=C_datedelta.days + 1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        for message in response.context['messages']:
            self.assertEqual(message.tags, 'error')
        self.assertTrue(Lesson.objects.count() == lesson_amount + 1)

    def test_of_high_cost(self):
        """ The check of salary is high in the morning and in the evening """

        form_data = {
            'student': self.student.id,
            'time': С_morning_time_markup.hour - 1,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        lesson_salary = Lesson.objects.get(
            time=time(form_data['time']),
            date=form_data['date']
        ).salary
        self.assertEqual(lesson_salary, C_salary_high)

        form_data = {
            'student': self.student.id,
            'time': С_morning_time_markup.hour,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        lesson_salary = Lesson.objects.get(
            time=time(form_data['time']),
            date=form_data['date']
        ).salary
        self.assertEqual(lesson_salary, C_salary_common)

        form_data = {
            'student': self.student.id,
            'time': C_evening_time_markup.hour,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        lesson_salary = Lesson.objects.get(
            time=time(form_data['time']),
            date=form_data['date']
        ).salary
        self.assertEqual(lesson_salary, C_salary_common)

        form_data = {
            'student': self.student.id,
            'time': C_evening_time_markup.hour + 1,
            'date': date.today() + timedelta(days=1)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        lesson_salary = Lesson.objects.get(
            time=time(form_data['time']),
            date=form_data['date']
        ).salary
        self.assertEqual(lesson_salary, C_salary_high)

    def test_salary_threshold_lesson(self):
        """ The check of salary threshold lesson """

        for hour in range(С_morning_time_markup.hour,
                          C_lesson_threshold - 2 + С_morning_time_markup.hour):
            form_data = {
                'student': self.student.id,
                'time': hour,
                'date': date.today() + timedelta(days=4)
            }
            response = self.client.post(
                path=self.path,
                data=form_data,
                follow=True
            )
            self.assertEqual(response.status_code, 200)

        form_data = {
            'student': self.student.id,
            'time': C_lesson_threshold - 1 + С_morning_time_markup.hour,
            'date': date.today() + timedelta(days=4)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        lesson_salary = Lesson.objects.get(
            time=time(form_data['time']),
            date=form_data['date']
        ).salary
        self.assertEqual(lesson_salary, C_salary_common)

        form_data = {
            'student': self.student.id,
            'time': C_lesson_threshold + С_morning_time_markup.hour,
            'date': date.today() + timedelta(days=4)
        }
        response = self.client.post(
            path=self.path,
            data=form_data,
            follow=True
        )
        lesson_salary = Lesson.objects.get(
            time=time(form_data['time']),
            date=form_data['date']
        ).salary
        self.assertEqual(lesson_salary, C_salary_high)

    def test_time_before_onset(self):
        """ The check error receiving when hour before the lesson is bigger
        than constraint """

        now = datetime.now().hour
        if now < C_evening_time.hour - C_timedelta.seconds//3600:
            lesson_amount = Lesson.objects.count()
            form_data = {
                'student': self.student.id,
                'time': now + C_timedelta.seconds//3600,
                'date': date.today()
            }
            response = self.client.post(
                path=self.path,
                data=form_data,
                follow=True
            )
            for message in response.context['messages']:
                self.assertEqual(message.tags, 'error')
            self.assertTrue(Lesson.objects.count() == lesson_amount)
