from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from yoyaku.tests.factories import StaffFactory, SuperUserFactory


class AuthViewTestCase(TestCase):

    fixtures = ['accounts', 'mail']

    @classmethod
    def setUpTestData(cls):
        cls.superuser = SuperUserFactory(user_id='superuser')
        cls.staff = StaffFactory(user_id='staff')

    def login(self, user_id='staff', password='password'):
        return self.client.login(user_id=user_id, password=password)

    def logout(self):
        return self.client.logout()

    def login_superuser(self):
        self.login(user_id=self.superuser.user_id)

    def assert_login_required(self, path, data=None):
        self.logout()
        res = self.client.get(path, data)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.url.startswith(reverse(settings.LOGIN_URL)))


class FormTestCase(TestCase):

    fixtures = ['accounts', 'mail']


class ModelTestCase(TestCase):

    fixtures = ['accounts', 'mail']
