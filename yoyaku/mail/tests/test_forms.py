from yoyaku.mail.forms import AddressCreateUpdateForm, SendMailForm, SystemMailUpdateForm
from yoyaku.mail.models import MailAddress
from yoyaku.tests.factories import MailAddressFactory
from yoyaku.tests.test_case import FormTestCase


class TestAddressCreateUpdateForm(FormTestCase):
    def test_save(self):
        data = {'email': 'test@example.com'}
        form = AddressCreateUpdateForm(data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(MailAddress.objects.filter(email=obj.email).count(), 1)

    def test_is_required_or_not(self):
        form = AddressCreateUpdateForm({})
        self.assertTrue(form.has_error('email', code='required'))
        self.assertFalse(form.has_error('memo', code='required'))

    def test_clean_email(self):
        data = {'email': 'Test@Example.COM'}
        form = AddressCreateUpdateForm(data)
        obj = form.save()
        self.assertEqual(obj.email, data['email'].lower())

    def test_email_unique(self):
        mail = MailAddressFactory()
        data = {'email': mail.email}
        form = AddressCreateUpdateForm(data)
        self.assertTrue(form.has_error('email', code='unique'))


class TestSystemMailUpdateForm(FormTestCase):
    def test_is_required_or_not(self):
        form = SystemMailUpdateForm({})
        self.assertFalse(form.has_error('sender', code='required'))
        self.assertFalse(form.has_error('subject', code='required'))
        self.assertFalse(form.has_error('memo', code='required'))


class TestSendMailForm(FormTestCase):
    def test_is_required_or_not(self):
        form = SendMailForm({})
        self.assertTrue(form.has_error('sender', code='required'))
        self.assertFalse(form.has_error('subject', code='required'))
        self.assertFalse(form.has_error('memo', code='required'))
