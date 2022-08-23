from django.core import mail

from yoyaku.mail.models import SystemMail
from yoyaku.tests.factories import BookingFactory, MailAddressFactory
from yoyaku.tests.test_case import ModelTestCase


class TestSystemMailManager(ModelTestCase):
    def test_get_registered_mail(self):
        obj = SystemMail.objects.get_registered_mail()
        self.assertEqual(1, obj.id)
        self.assertEqual('顧客登録完了メール', obj.name)


class TestSystemMail(ModelTestCase):
    def test_replace_mail_tags(self):
        booking = BookingFactory()
        system_mail = SystemMail.objects.get_registered_mail()
        text = '__NAME__,__MAILADDRESS__,__TEL__,__RESERVATION_DATE__'
        system_mail.subject = system_mail.content = text

        system_mail.replace_mail_tags(booking)

        customer = booking.customer
        bl = booking.booking_limit
        expected = f'{customer.username},{customer.email},{customer.phone_number},{bl.formatted_start_datetime()}'
        self.assertEqual(expected, system_mail.subject)
        self.assertEqual(expected, system_mail.content)

    def test_send_mail(self):
        booking = BookingFactory()
        system_mail = SystemMail.objects.get_registered_mail()
        system_mail.sender = MailAddressFactory()
        system_mail.subject = system_mail.content = '__NAME__'

        system_mail.send_system_mail(booking)

        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.subject, booking.customer.username)
        self.assertEqual(m.body, booking.customer.username)
