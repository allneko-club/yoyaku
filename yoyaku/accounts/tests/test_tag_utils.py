from datetime import timedelta

from django.test import TestCase

from yoyaku.accounts.models import User
from yoyaku.accounts.templatetags.tag_utils import *
from yoyaku.booking.forms import UpdateStaffForm
from yoyaku.booking.utils import get_today0000
from yoyaku.tests.factories import BookingFactory


class TestDaysSince(TestCase):
    """days_since_filter()のテスト"""
    
    def test_valid_value(self):
        test_datetime = get_today0000()
        self.assertEqual(days_since_filter(test_datetime), '0日')

        test_datetime -= timedelta(days=1)
        self.assertEqual(days_since_filter(test_datetime), '1日')

    def test_invalid_value(self):
        self.assertEqual(days_since_filter(''), '')
        self.assertEqual(days_since_filter('invalid_type'), '')


class TestGetUsernames(TestCase):

    def test_success(self):
        booking = BookingFactory()
        staff_choices = [('', '未定義')]
        staff_choices.extend(list(User.staffs.is_active().values_list('id', 'username')))
        update_staff_form_list = [UpdateStaffForm(choices=staff_choices, initial={'staff': booking.staff_id})]
        result = str(get_usernames(update_staff_form_list, 0)).replace('\n', '').replace(' ', '')
        expected = f'<selectname="staff"class="form-controlselect-staff"requiredid="id_staff">' \
                   f'<optionvalue="">未定義</option><optionvalue="1"selected>{booking.get_staff_name()}</option>' \
                   f'</select>'
        self.assertEqual(result, expected)
