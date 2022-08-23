from yoyaku.mail.models import SystemMail
from yoyaku.mail.send_mails import send_customer_registered_mail
from yoyaku.tests.factories import BookingFactory, MailAddressFactory
from yoyaku.tests.test_case import ModelTestCase


class TestSendMails(ModelTestCase):
    def setUp(self):
        self.system_mail = SystemMail.objects.get_registered_mail()
        self.system_mail.sender = MailAddressFactory()
        self.system_mail.save()

    def test_send_customer_registered_mail(self):
        booking = BookingFactory()
        result = send_customer_registered_mail(booking)
        self.assertTrue(result)
