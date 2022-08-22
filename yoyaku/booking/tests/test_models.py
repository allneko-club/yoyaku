from datetime import datetime, timedelta

from django.test import TestCase
from django.utils.timezone import now, utc

from yoyaku.booking.models import BookingLimit
from yoyaku.tests.factories import BookingFactory, BookingLimitFactory, StaffFactory


class TestBookingLimitManager(TestCase):

    def test_can_book(self):
        bl_cannot_book = BookingLimitFactory(limit=1, start_datetime=now())
        bl_cannot_book2 = BookingLimitFactory(limit=0, start_datetime=now()+timedelta(minutes=60))
        bl_can_select = BookingLimitFactory(limit=1, start_datetime=now()+timedelta(minutes=60))
        bl_list = BookingLimit.objects.can_book()
        self.assertEqual(bl_list.count(), 1)
        self.assertEqual(bl_list.last(), bl_can_select)

        bl_list = BookingLimit.objects.can_book(include=bl_cannot_book2)
        self.assertEqual(bl_list.count(), 2)

    def test_customers_can_select(self):
        bl_cannot_select = BookingLimitFactory(limit=1, start_datetime=now())
        bl_can_select = BookingLimitFactory(limit=1, start_datetime=now()+timedelta(minutes=60))
        bl_list = BookingLimit.objects.customers_can_select(after_min=30)
        self.assertEqual(bl_list.count(), 1)
        self.assertEqual(bl_list.last(), bl_can_select)


class TestBookingLimit(TestCase):

    def setUp(self):
        self.bl = BookingLimitFactory(limit=1, start_datetime=datetime(2020, 1, 1, tzinfo=utc))

    def test_formatted_start_datetime(self):
        self.assertEqual(self.bl.formatted_start_datetime(), '2020年01月01日 09時00分')

    def test_str(self):
        self.assertEqual(str(self.bl), '開始日時：2020-01-01 09:00 予約状況：0 / 1')

    def test_is_filled(self):
        booking = BookingFactory(booking_limit=self.bl)
        self.bl.refresh_from_db()
        self.assertTrue(self.bl.is_filled())
        self.assertFalse(self.bl.is_filled(exclude=booking))

    def test_booked_count(self):
        self.assertEqual(self.bl.booked_count, 0)

        BookingFactory(booking_limit=self.bl)
        self.bl.refresh_from_db()
        self.assertEqual(self.bl.booked_count, 1)

    def test_get_state(self):
        params = [
            (0, 0, '×'), (2, 0, '●'), (2, 1, '▲'), (3, 3, '×'), (4, 1, '●'),
            (4, 2, '▲'), (5, 2, '●'), (5, 3, '▲'), (6, 5, '▲'),
        ]
        for limit, booked, expected in params:
            bl = BookingLimitFactory(limit=limit, start_datetime=now())
            for i in range(booked):
                booking = BookingFactory(booking_limit=bl)

            with self.subTest(expected=expected):
                assert bl.get_state() == expected


class TestBookingModel(TestCase):

    def setUp(self):
        self.bl = BookingLimitFactory(limit=1, start_datetime=datetime(2020, 1, 1, tzinfo=utc))
        self.booking = BookingFactory(booking_limit=self.bl, staff=None)

    def test_get_staff_name(self):
        self.assertEqual(self.booking.get_staff_name(), '未定義')

        booking = BookingFactory()
        self.assertEqual(booking.get_staff_name(), booking.staff.username)

    def test_get_start_datetime(self):
        self.assertEqual(self.booking.get_start_datetime(), self.bl.start_datetime)

    def test_is_updated_by_others(self):
        user1 = StaffFactory()
        user2 = StaffFactory()

        dt_before_save = now()
        self.booking.updated_by = user1
        self.booking.save()
        dt_after_save = now()

        self.assertFalse(self.booking.is_updated_by_others(dt_before_save, user1))
        self.assertFalse(self.booking.is_updated_by_others(dt_after_save, user1))
        self.assertTrue(self.booking.is_updated_by_others(dt_before_save, user2))
        self.assertFalse(self.booking.is_updated_by_others(dt_after_save, user2))
