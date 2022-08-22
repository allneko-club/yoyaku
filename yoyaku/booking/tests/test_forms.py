from datetime import datetime, timedelta, timezone

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase
from django.utils.timezone import now, utc

from yoyaku.booking.forms import BookingForm, BookingLimitEditForm, RegisterBookingForm, copy_boolean_field
from yoyaku.booking.models import BookingLimit
from yoyaku.booking.utils import get_today0000
from yoyaku.tests.factories import BookingFactory, BookingLimitFactory, CustomerFactory, StaffFactory


class TestMethods(TestCase):
    def test_copy_boolean_field(self):
        copied = forms.BooleanField(label='9:00~9:30')
        time1000 = copy_boolean_field(copied, '10:00~10:30')
        self.assertEqual(time1000.label, '10:00~10:30')


class TestBookingLimitEditForm(TestCase):

    def test_create(self):
        data = {
            'start_datetime': '2020-01-01',
            'end_datetime': '2020-01-02',
            'limit': 1,
            'time0900': True,
            'time1000': True,
        }
        form = BookingLimitEditForm(data)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(BookingLimit.objects.count(), 4)
        obj1 = BookingLimit.objects.get(start_datetime='2020-01-01 00:00:00+00:00')
        obj2 = BookingLimit.objects.get(start_datetime='2020-01-02 00:00:00+00:00')
        obj3 = BookingLimit.objects.get(start_datetime='2020-01-02 01:00:00+00:00')
        obj4 = BookingLimit.objects.get(start_datetime='2020-01-02 01:00:00+00:00')
        self.assertEqual(obj1.limit, 1)
        self.assertEqual(obj2.limit, 1)
        self.assertEqual(obj3.limit, 1)
        self.assertEqual(obj4.limit, 1)

    def test_update(self):
        bl = BookingLimitFactory(limit=1, start_datetime=datetime(2020, 1, 1, tzinfo=utc))
        data = {
            'start_datetime': '2020-01-01',
            'end_datetime': '2020-01-01',
            'limit': 3,
            'time0900': True,
        }
        form = BookingLimitEditForm(data)
        self.assertTrue(form.is_valid())
        form.save()

        bl.refresh_from_db()
        self.assertEqual(bl.limit, 3)
        self.assertEqual(bl.start_datetime, datetime(2020, 1, 1, tzinfo=timezone.utc))

    def test_required(self):
        form = BookingLimitEditForm({})
        for required_field in ('start_datetime', 'end_datetime', 'limit'):
            with self.subTest(required_field=required_field):
                self.assertTrue(form.has_error(required_field, code='required'))
        self.assertEqual(len(form.errors), 3)

    def test_start_date_end_date_is_same(self):
        data = {
            'start_datetime': '2020-01-01',
            'end_datetime': '2020-01-01',
            'limit': 1,
            'time0900': True,
        }
        form = BookingLimitEditForm(data)
        self.assertTrue(form.is_valid())

    def test_start_date_is_bigger_than_end_date(self):
        data = {
            'start_datetime': '2020-02-01',
            'end_datetime': '2020-01-01',
            'limit': 1,
            'time0900': True,
        }
        form = BookingLimitEditForm(data)
        self.assertTrue(form.has_error('start_datetime', code='out_of_date'))

    def test_invalid_limit(self):
        """ 異常系 枠数が０未満 """
        data = {
            'start_datetime': '2020-01-01',
            'end_datetime': '2020-01-01',
            'limit': -1,
            'time0900': True,
        }
        form = BookingLimitEditForm(data)
        self.assertTrue(form.has_error('limit', code='min_value'))

    def test_booking_overflow_error(self):
        """予約枠数を予約数未満に変更する"""
        bl = BookingLimitFactory(limit=1, start_datetime=datetime(2020, 1, 1, tzinfo=utc))
        BookingFactory(booking_limit=bl)
        data = {
            'start_datetime': '2020-01-01',
            'end_datetime': '2020-01-01',
            'limit': 0,
            'time0900': True,
        }
        form = BookingLimitEditForm(data)
        self.assertTrue(form.has_error(NON_FIELD_ERRORS, code='booking_overflow'))


class TestBookingForm(TestCase):

    def setUp(self):
        self.staff = StaffFactory()
        self.customer = CustomerFactory()
        self.bl = BookingLimitFactory(limit=10, start_datetime=get_today0000() + timedelta(days=1, hours=9))
        self.bl_empty = BookingLimitFactory(limit=0, start_datetime=get_today0000() + timedelta(days=1, hours=10))

    def test_save_if_booking_limit_not_exist(self):
        """指定した日時の予約枠がない場合、予約枠を新規作成し、予約を作成する"""
        data = {
            'staff': self.staff,
            'customer': self.customer.id,
            'start_datetime': '2021-07-02T12:00:00+09:00',
            'select_booking_limit': False,
        }
        form = BookingForm(data)
        self.assertTrue(form.is_valid())
        obj = form.save(self.staff)

        new_bl = BookingLimit.objects.all().last()
        self.assertEqual(new_bl.start_datetime, datetime(2021, 7, 2, 3, tzinfo=utc))
        self.assertEqual(new_bl.limit, 1)
        self.assertEqual(obj.booking_limit, new_bl)
        self.assertEqual(obj.customer, self.customer)
        self.assertEqual(obj.staff, self.staff)
        self.assertEqual(obj.updated_by, self.staff)

    def test_save_if_booking_limit_exist(self):
        """カレンダーから予約枠作成済みの日時を選んだ時のテスト"""
        data = {
            'staff': self.staff.id,
            'customer': self.customer.id,
            'start_datetime': self.bl.start_datetime,
            'select_booking_limit': False,
        }
        form = BookingForm(data)
        self.assertTrue(form.is_valid())
        obj = form.save(self.staff)

        self.assertEqual(obj.booking_limit, self.bl)
        self.assertEqual(obj.customer, self.customer)
        self.assertEqual(obj.staff, self.staff)
        self.assertEqual(obj.updated_by, self.staff)

    def test_save_if_select_booking_limit_is_checked(self):
        data = {
            'staff': self.staff.id,
            'customer': self.customer.id,
            'select_booking_limit': True,
            'booking_limit': self.bl.id,
        }
        form = BookingForm(data)
        self.assertTrue(form.is_valid())
        obj = form.save(self.staff)

        self.assertEqual(obj.booking_limit, self.bl)
        self.assertEqual(obj.customer, self.customer)
        self.assertEqual(obj.staff, self.staff)
        self.assertEqual(obj.updated_by, self.staff)

    def test_invalid_choice_error_in_booking_limit(self):
        """リストから選択した予約枠が満席の場合"""
        booking = BookingFactory()
        booking_limit = booking.booking_limit
        booking_limit.limit = 1
        booking_limit.save()
        data = {
            'staff': self.staff.id,
            'customer': self.customer.id,
            'select_booking_limit': True,
            'booking_limit': booking.booking_limit.id,
        }
        form = BookingForm(data)
        self.assertTrue(form.has_error('booking_limit', code='invalid_choice'))

    def test_booking_time_error(self):
        data = {
            'staff': self.staff.id,
            'customer': self.customer.id,
            'start_datetime': '2021-07-02T00:00:00+09:00',
            'select_booking_limit': False,
        }
        form = BookingForm(data)
        self.assertTrue(form.has_error('start_datetime', code='booking_time'))

    def test_select_filled_datetime_from_calendar(self):
        """カレンダーから選択した予約枠が満席の場合"""
        data = {
            'staff': self.staff.id,
            'customer': self.customer.id,
            'start_datetime': self.bl_empty.start_datetime,
            'select_booking_limit': False,
        }
        form = BookingForm(data)
        self.assertTrue(form.has_error('start_datetime', code='booking_filled'))

    def test_select_filled_datetime_from_list(self):
        data = {
            'staff': self.staff.id,
            'customer': self.customer.id,
            'start_datetime': '2021-07-02T00:00:00+09:00',
            'select_booking_limit': True,
            'booking_limit': self.bl_empty.id,
        }
        form = BookingForm(data)
        self.assertTrue(form.has_error('booking_limit', code='invalid_choice'))

    def test_booking_limit_queryset_if_instance_exist(self):
        """formのinstanceに関連するBookingLimitはquerysetに含まれていないテスト"""
        booking = BookingFactory()
        data = {
            'staff': self.staff,
            'customer': self.customer.id,
            'start_datetime': '2021-07-02T12:00:00+09:00',
            'select_booking_limit': False,
        }
        form = BookingForm(data, instance=booking)
        self.assertEqual(form.fields['booking_limit'].queryset.count(), 1)
        bl = form.fields['booking_limit'].queryset.last()
        self.assertEqual(bl, self.bl)


class TestRegisterBookingForm(TestCase):

    def setUp(self):
        self.bl = BookingLimitFactory(limit=1, start_datetime=now())

    def test_save(self):
        bl = BookingLimitFactory(limit=1, start_datetime=now()+timedelta(hours=5))
        customer = CustomerFactory()
        data = {'booking_limit': bl.id}
        form = RegisterBookingForm(data)
        self.assertTrue(form.is_valid())
        obj = form.save(customer)
        self.assertEqual(obj.customer, customer)
        self.assertEqual(obj.booking_limit, bl)

    def test_invalid_choice_error(self):
        data = {'booking_limit': 0}
        form = RegisterBookingForm(data)
        self.assertTrue(form.has_error('booking_limit', code='invalid_choice'))

    def test_out_of_date_error(self):
        data = {'booking_limit': self.bl.id}
        form = RegisterBookingForm(data)
        self.assertTrue(form.has_error('booking_limit', code='out_of_date'))

    def test_filled_error(self):
        BookingFactory(booking_limit=self.bl)
        data = {'booking_limit': self.bl.id}
        form = RegisterBookingForm(data)
        self.assertTrue(form.has_error('booking_limit', code='filled'))

# todo TestBookingSearchForm
