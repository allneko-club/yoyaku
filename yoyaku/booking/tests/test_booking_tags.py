from datetime import timedelta

from django.test import override_settings, TestCase

from yoyaku.booking.templatetags.booking_tags import create_rows
from yoyaku.booking.models import BookingLimit
from yoyaku.booking.utils import get_today0000
from yoyaku.tests.factories import BookingLimitFactory


class TestMethods(TestCase):

    @override_settings(DISP_DAYS=2, START_TIME='09:00', END_TIME='10:00')
    def test_create_rows(self):
        start_datetime = get_today0000() + timedelta(hours=9)
        BookingLimitFactory(limit=1, start_datetime=start_datetime)
        limit_list = BookingLimit.objects.all()
        result = create_rows(limit_list, start_datetime)

        expected = '<tr><td>9:00~9:30</td><td>0 / 1</td><td></td></tr><tr><td>9:30~10:00</td><td></td><td></td></tr>' \
                   '<tr><td>合計</td><td>0 / 1</td><td>0 / 0</td></tr>'
        self.assertEqual(result, expected)