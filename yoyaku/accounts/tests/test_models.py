from django.test import TestCase

from yoyaku.accounts.models import User
from yoyaku.tests.test_case import ModelTestCase
from yoyaku.tests.factories import UserFactory, CustomerFactory, StaffFactory,SuperUserFactory


class TestStaffManager(ModelTestCase):
    def setUp(self):
        self.superuser = SuperUserFactory()
        self.staff = StaffFactory()
        self.customer = CustomerFactory()

    def test_get_queryset(self):
        staff_list = User.staffs.all()
        self.assertEqual(staff_list.count(), 1)
        self.assertFalse(staff_list[0].is_superuser)
        self.assertTrue(staff_list[0].is_staff)

    def test_is_active(self):
        self.staff_not_active = StaffFactory(is_active=False)
        staff_list = User.customers.is_active()
        self.assertEqual(staff_list.count(), 1)
        self.assertTrue(staff_list[0].is_active)


class TestCustomerManager(ModelTestCase):

    def setUp(self):
        self.superuser = SuperUserFactory()
        self.staff = StaffFactory()
        self.customer = CustomerFactory()

    def test_get_queryset(self):
        customer_list = User.customers.all()
        self.assertEqual(customer_list.count(), 1)
        self.assertFalse(customer_list[0].is_superuser)
        self.assertFalse(customer_list[0].is_staff)

    def test_is_active(self):
        self.customer_not_active = CustomerFactory(is_active=False)
        customer_list = User.customers.is_active()
        self.assertEqual(customer_list.count(), 1)
        self.assertTrue(customer_list[0].is_active)


class TestUser(TestCase):

    def setUp(self):
        self.user = UserFactory()

    def test_get_full_name(self):
        self.assertEqual(self.user.get_full_name(), self.user.username)

    def test_get_short_name(self):
        self.assertEqual(self.user.get_full_name(), self.user.username)
