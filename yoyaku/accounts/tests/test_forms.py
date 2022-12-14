from django.test import TestCase
from django.contrib.auth import authenticate

from yoyaku.accounts.forms import CustomerForm, StaffForm, RegisterCustomerForm
from yoyaku.tests.factories import CustomerFactory, StaffFactory


class TestStaffForm(TestCase):
    def test_create(self):
        data = {
            'user_id': 'abc',
            'username': 'abc',
            'password1': '5tgbnhy6',
            'password2': '5tgbnhy6',
        }
        form = StaffForm(data)
        user = form.save()
        self.assertTrue(user.is_staff)

    def test_update(self):
        user1 = StaffFactory()
        data = {
            'user_id': 'new_user_id',
            'username': 'new_username',
            'password1': '5tgbnhy6',
            'password2': '5tgbnhy6',
        }
        form = StaffForm(data, instance=user1)
        user = form.save()
        self.assertEqual(user.user_id, 'new_user_id')
        self.assertEqual(user.username, 'new_username')

    def test_created_staff_can_login(self):
        form = StaffForm({
            'user_id': 'abc',
            'username': 'abc',
            'password1': '5tgbnhy6',
            'password2': '5tgbnhy6',
        })
        user = form.save()
        self.assertIsNotNone(authenticate(user_id=user.user_id, password='5tgbnhy6'))

    def test_is_required_or_not(self):
        form = StaffForm({})
        for i in ['user_id', 'username', 'password1', 'password2']:
            with self.subTest(i=i):
                self.assertTrue(form.has_error(i, code='required'))

    def test_password1_maxlength(self):
        data = {
            'user_id': 'test',
            'username': 'test',
            'password1': 'passw0rd' + 'a' * 120,
            'password2': 'passw0rd' + 'a' * 120,
        }
        form = StaffForm(data)
        self.assertTrue(form.is_valid())

        data['password1'] += 'a'
        form = StaffForm(data)
        self.assertTrue(form.has_error('password1', code='max_length'))
        self.assertFalse(form.has_error('password2', code='max_length'))

    def test_password2_mismatch_error(self):
        data = {
            'user_id': 'test',
            'username': 'test',
            'password1': 'passw0rd',
            'password2': 'passw0rd1',
        }
        form = StaffForm(data)
        self.assertTrue(form.has_error('password2', code='password_mismatch'))

    def test_user_id_is_unique(self):
        user = StaffFactory()
        data = {
            'user_id': user.user_id,
            'username': 'abc',
            'password1': '5tgbnhy6',
            'password2': '5tgbnhy6',
        }
        form = StaffForm(data)
        self.assertTrue(form.has_error('user_id', code='unique'))

    def test_invalid_character_in_user_id(self):
        data = {
            'user_id': 'abc',
            'username': 'abc',
            'password1': '5tgbnhy6',
            'password2': '5tgbnhy6',
        }
        for invalid_user_id in ('???', '%'):
            with self.subTest(invalid_user_id=invalid_user_id):
                data['user_id'] = invalid_user_id
                form = StaffForm(data)
                self.assertTrue(form.has_error('user_id', code='invalid_character'))


class TestCustomerForm(TestCase):
    """
    ?????????????????????????????????????????????????????????????????????
    """

    fixtures = ['accounts', 'mail']

    def test_create(self):
        data = {
            'username': '????????????',
            'email': 'test@example.com',
            'phone_number': '12345678901',
        }
        form = CustomerForm(data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.username, '????????????')
        self.assertTrue(obj.user_id)

    def test_update(self):
        customer = CustomerFactory()
        data = {
            'username': customer.username,
            'email': 'test-update@example.com',
            'phone_number': customer.phone_number,
        }
        form = CustomerForm(data, instance=customer)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.email, 'test-update@example.com')

    def test_is_required_or_not(self):
        form = CustomerForm({})
        for required_field in ('username', 'email', 'phone_number'):
            with self.subTest(required_field=required_field):
                self.assertTrue(form.has_error(required_field, code='required'))

        not_required_fields = ('furigana', 'linename', 'age', 'ages', 'job', 'zip_code', 'zip',
                               'side_business_experience', 'workable_time', 'contact', 'memo1', 'memo2')
        for not_required_field in not_required_fields:
            with self.subTest(not_required_field=not_required_field):
                self.assertFalse(form.has_error(not_required_field, code='required'))

    def test_unique_error(self):
        """?????????????????????????????????????????????????????????"""
        customer = CustomerFactory()
        data = {
            'username': customer.username,
            'email': customer.email,
            'phone_number': customer.phone_number,
        }
        form = CustomerForm(data)
        self.assertTrue(form.has_error('phone_number', code='unique'))
        self.assertTrue(form.has_error('email', code='unique'))

    def test_invalid_username(self):
        data = {
            'username': '%%',
            'email': 'test@example.com',
            'phone_number': '12345678901',
        }
        form = CustomerForm(data)
        self.assertTrue(form.has_error('username', code='invalid'))

    def test_clean_username(self):
        data = {
            'username': '???????????????',
            'email': 'test@example.com',
            'phone_number': '12345678901',
        }
        form = CustomerForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], '????????????')

    def test_clean_email(self):
        data = {
            'username': '???????????????',
            'email': 'Test@Example.COM',
            'phone_number': '12345678901',
        }
        form = CustomerForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')


class TestRegistCustomerForm(TestCase):
    def test_create(self):
        data = {
            'username': '??????',
            'furigana': '?????????',
            'email': 'test@example.com',
            'phone_number': '12345678901',
            'age': 18,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.username, '??????')
        self.assertTrue(obj.user_id)

    def test_update(self):
        customer = CustomerFactory()
        data = {
            'username': customer.username,
            'furigana': '?????????',
            'email': 'test-update@example.com',
            'phone_number': customer.phone_number,
            'age': 18,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data, instance=customer)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.email, 'test-update@example.com')

    def test_is_required_or_not(self):
        form = RegisterCustomerForm({})
        for required_field in ('username', 'furigana', 'email', 'phone_number', 'age', 'job'):
            with self.subTest(required_field=required_field):
                self.assertTrue(form.has_error(required_field, code='required'))
        self.assertFalse(form.has_error('linename', code='required'))

    def test_unique_error(self):
        """?????????????????????????????????????????????????????????"""
        customer = CustomerFactory()
        data = {
            'username': '??????',
            'furigana': '?????????',
            'email': customer.email,
            'phone_number': customer.phone_number,
            'linename': 'linename',
            'age': 18,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data)
        self.assertEqual(len(form.errors), 2)
        self.assertTrue(form.has_error('phone_number', code='unique'))
        self.assertTrue(form.has_error('email', code='unique'))


    def test_clean_username(self):
        data = {
            'username': ' ???    ?????? ??????????????? ?????? ???',
            'furigana': '?????????',
            'email': 'test@example.com',
            'phone_number': '12345678901',
            'age': 18,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], '????????????????????????')

    def test_clean_furigana(self):
        data = {
            'username': '??????',
            'furigana': ' ?????????????????? ???????????????',
            'email': 'test@example.com',
            'phone_number': '12345678901',
            'age': 18,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['furigana'], '????????????????????????')

    def test_clean_email(self):
        data = {
            'username': '??????',
            'furigana': '?????????',
            'email': 'Test@Example.COM',
            'phone_number': '12345678901',
            'age': 18,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')

    def test_age(self):
        data = {
            'username': '??????',
            'furigana': '?????????',
            'email': 'examplE@aa.bb',
            'phone_number': '12345678901',
            'linename': 'linename',
            'age': 17,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data)
        self.assertTrue(form.has_error('age', code='invalid_choice'))

        data['age'] = 18
        form = RegisterCustomerForm(data)
        self.assertFalse(form.errors)

        data['age'] = 85
        form = RegisterCustomerForm(data)
        self.assertFalse(form.errors)

        data['age'] = 86
        form = RegisterCustomerForm(data)
        self.assertTrue(form.has_error('age', code='invalid_choice'))

    def test_invalid_phone_number(self):
        """
        ????????????????????????
        ?????????????????????11????????????
        """
        data = {
            'username': '??????',
            'furigana': '?????????',
            'email': 'examplE@aa.bb',
            'phone_number': 'abcd',
            'linename': 'linename',
            'age': 18,
            'job': '?????????',
        }
        form = RegisterCustomerForm(data)
        self.assertTrue(form.has_error('phone_number', code='phone_number_pattern'))

        # ????????????
        data['phone_number'] = '?????????????????????????????????'
        form = RegisterCustomerForm(data)
        self.assertTrue(form.has_error('phone_number', code='phone_number_pattern'))
