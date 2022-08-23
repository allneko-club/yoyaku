from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from django.utils.timezone import now, zoneinfo

from yoyaku.booking.utils import (date_range, get_disp_hour_from, get_disp_hour_to, get_today0000,
                                  is_valid_booking_time, is_valid_hour, is_valid_minute)


class TestBookingUtils(TestCase):

    def test_is_valid_hour(self):
        self.assertFalse(is_valid_hour(datetime(2000, 1, 1, get_disp_hour_from() - 1)))
        self.assertTrue(is_valid_hour(datetime(2000, 1, 1, get_disp_hour_from())))
        self.assertTrue(is_valid_hour(datetime(2000, 1, 1, get_disp_hour_from() + 1)))
        self.assertTrue(is_valid_hour(datetime(2000, 1, 1, get_disp_hour_to() - 1)))
        self.assertFalse(is_valid_hour(datetime(2000, 1, 1, get_disp_hour_to())))

    def test_is_valid_minute(self):
        self.assertTrue(is_valid_minute(datetime(2000, 1, 1, 9, 0)))
        self.assertFalse(is_valid_minute(datetime(2000, 1, 1, 9, 10)))
        self.assertFalse(is_valid_minute(datetime(2000, 1, 1, 9, 5)))
        self.assertTrue(is_valid_minute(datetime(2000, 1, 1, 9, 30)))

    def test_is_validate_booking_time(self):
        self.assertFalse(is_valid_booking_time(datetime(2000, 1, 1, 8, 30)))
        self.assertTrue(is_valid_booking_time(datetime(2000, 1, 1, 9, 0)))
        self.assertTrue(is_valid_booking_time(datetime(2000, 1, 1, 9, 30)))
        self.assertTrue(is_valid_booking_time(datetime(2000, 1, 1, 21, 30)))
        self.assertFalse(is_valid_booking_time(datetime(2000, 1, 1, 22, 0)))

    def test_date_range(self):
        start = datetime.today()
        end = start + timedelta(days=3)
        for i, result in enumerate(date_range(start, end)):
            with self.subTest(result=result):
                self.assertEqual(start + timedelta(days=i), result)

    @override_settings(TIME_ZONE='Asia/Tokyo')
    def test_get_today0000(self):
        result = get_today0000()
        expected = now()
        self.assertEqual(expected.year, result.year)
        self.assertEqual(expected.month, result.month)
        self.assertEqual(expected.day, result.day)
        self.assertEqual(0, result.hour)
        self.assertEqual(0, result.minute)
        self.assertEqual(0, result.second)
        self.assertEqual(0, result.microsecond)
        self.assertEqual(zoneinfo.ZoneInfo('Asia/Tokyo'), result.tzinfo)