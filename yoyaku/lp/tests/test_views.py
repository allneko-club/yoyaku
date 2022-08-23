from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from yoyaku.accounts.forms import RegisterCustomerForm
from yoyaku.accounts.models import User
from yoyaku.booking.forms import RegisterBookingForm
from yoyaku.booking.models import Booking
from yoyaku.booking.utils import get_today0000
from yoyaku.mail.models import SystemMail
from yoyaku.tests.factories import BookingLimitFactory, MailAddressFactory


class TestBookingView(TestCase):

    fixtures = ['mail']

    def setUp(self):
        # 予約枠作成 翌日9:00~の枠を1つ作成
        self.bl = BookingLimitFactory(limit=1, start_datetime=(get_today0000() + timedelta(days=1, hours=9)))

        address = MailAddressFactory()
        system_mail = SystemMail.objects.get(name='顧客登録完了メール')
        system_mail.sender = address
        system_mail.subject = '__NAME__'
        system_mail.content = '__NAME__'
        system_mail.save()
        self.viewname = 'lp:予約フォーム'

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'lp/booking_form.html')
        self.assertEqual(len(res.context['booking_limit_list']), 1)
        self.assertTrue(isinstance(res.context['form'], RegisterCustomerForm))
        self.assertTrue(isinstance(res.context['form2'], RegisterBookingForm))

    @override_settings(HOSTNAME='example.com')
    def test_post_success(self):
        """顧客登録、予約登録のテスト"""
        # 予約枠作成 翌日9:00~の枠を1つ作成
        res = self.client.post(
            reverse(self.viewname),
            {
                'username': 'てすと',
                'furigana': 'テスト',
                'email': 'test@example.com',
                'age': 40,
                'job': '社長',
                'phone_number': '01234567890',
                'booking_limit': self.bl.id,
            },
        )
        customer = User.customers.get(email='test@example.com')
        self.assertEqual(Booking.objects.filter(customer=customer).count(), 1)
        self.assertRedirects(res, reverse('lp:予約完了'))

    @override_settings(HOSTNAME='example.com')
    def test_send_mail(self):
        """登録時に送信されるメールのテスト メールのタグ変換テスト"""
        res = self.client.post(
            reverse(self.viewname),
            {
                'username': 'てすと',
                'furigana': 'テスト',
                'email': 'test@example.com',
                'age': 40,
                'job': '会社員',
                'phone_number': '01234567890',
                'booking_limit': self.bl.id,
            },
        )
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.subject, 'てすと')
        self.assertEqual(m.body, 'てすと')

    @override_settings(HOSTNAME='example.com')
    def test_form_error(self):
        """顧客情報のエラーと予約枠のエラーが発生するテスト"""
        res = self.client.post(
            reverse(self.viewname),
            {
                'username': 'てすと',
                'furigana': 'テスト',
                'email': '',
                'age': 40,
                'job': '会社員',
                'phone_number': '01234567890',
                'booking_limit': 5,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['form'].has_error('email', 'required'))
        self.assertTrue(res.context['form2_errors'].has_error('booking_limit', 'invalid_choice'))


class TestBookingDoneView(TestCase):
    @override_settings(HOSTNAME='example.com')
    def test_get(self):
        res = self.client.get(reverse('lp:予約完了'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'lp/booking_done.html')
