from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase
from django.urls import reverse

from yoyaku.authentication.forms import AuthenticationForm
from yoyaku.tests.factories import CustomerFactory, StaffFactory, SuperUserFactory
from yoyaku.tests.test_case import AuthViewTestCase


class TestUserLoginView(TestCase):
    def setUp(self):
        self.viewname = 'authentication:login'

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.context['form'], AuthenticationForm))
        self.assertTemplateUsed(res, 'accounts/login.html')

    def test_superuser_can_login(self):
        superuser = SuperUserFactory()
        res = self.client.post(reverse(self.viewname), {'username': superuser.user_id, 'password': 'password'})
        self.assertRedirects(res, reverse(settings.LOGIN_REDIRECT_URL))

    def test_staff_can_login(self):
        staff = StaffFactory()
        res = self.client.post(reverse(self.viewname), {'username': staff.user_id, 'password': 'password'})
        self.assertRedirects(res, reverse(settings.LOGIN_REDIRECT_URL))

    def test_customer_cant_login(self):
        customer = CustomerFactory()
        res = self.client.post(reverse(self.viewname), {'username': customer.user_id, 'password': 'password'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['form'].has_error(NON_FIELD_ERRORS, code='invalid_login'))


class TestUserLogoutView(AuthViewTestCase):
    def test_staff_can_logout(self):
        self.login()
        res = self.client.post(reverse('authentication:logout'))
        self.assertRedirects(res, reverse(settings.LOGOUT_REDIRECT_URL))
