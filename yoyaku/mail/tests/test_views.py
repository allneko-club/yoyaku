from unittest.mock import patch

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from yoyaku.mail.forms import AddressCreateUpdateForm, SendMailForm
from yoyaku.mail.models import MailAddress, SystemMail
from yoyaku.tests.factories import BookingFactory, BookingLimitFactory, MailAddressFactory, SystemMailFactory
from yoyaku.tests.test_case import AuthViewTestCase


class TestSystemMailListView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'mail:システムメール一覧'

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/systemmail_list.html')

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname))


class TestSystemMailUpdateView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.address = MailAddressFactory()
        self.viewname = 'mail:システムメール編集'

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[1]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/systemmail_form.html')

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname, args=[1]))

    def test_post_success(self):
        res = self.client.post(
            reverse(self.viewname, args=[1]),
            {
                'sender': self.address.id,
                'subject': '件名',
                'content': '本文',
            },
        )
        self.assertRedirects(res, reverse('mail:システムメール一覧'))

        updated = SystemMail.objects.get(id=1)
        self.assertEqual(updated.sender.email, self.address.email)
        self.assertEqual(updated.subject, '件名')
        self.assertEqual(updated.content, '本文')

    def test_post_invalid_data(self):
        res = self.client.post(
            reverse(self.viewname, args=[1]),
            {'sender': 0},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/systemmail_form.html')
        self.assertTrue(res.context['form'].non_field_errors())

    def test_select_not_exist_object(self):
        # 存在しないsystem_mailを指定したときのテスト
        res = self.client.post(
            reverse(self.viewname, args=[0]),
            {'sender': self.address.id},
        )
        self.assertEqual(res.status_code, 404)


class TestEditMailView(AuthViewTestCase):
    def setUp(self):
        self.login()
        self.viewname = 'mail:メール編集'
        self.system_mail = SystemMail.objects.get(name='顧客登録完了メール')
        self.address = MailAddressFactory()
        self.bl = BookingLimitFactory(limit=1, start_datetime=timezone.now())
        self.booking = BookingFactory(booking_limit=self.bl)

    @patch('yoyaku.mail.models.SystemMail.replace_mail_tags')
    def test_get(self, replace_mail_tags):
        """
        システムメールのタグを変換するメソッドを実行しているか
        """
        res = self.client.get(reverse(self.viewname, args=[self.system_mail.id, self.booking.id]))
        self.assertTemplateUsed(res, 'mail/edit_mail.html')
        self.assertEqual(res.context['object'], self.system_mail)
        self.assertEqual(res.context['booking'], self.booking)
        self.assertEqual(res.context['customer'], self.booking.customer)
        self.assertEqual(replace_mail_tags.call_count, 1)
        self.assertTrue(isinstance(res.context['form'], SendMailForm))

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname, args=[self.system_mail.id, self.booking.id]))

    def test_post_success(self):
        res = self.client.post(
            reverse(self.viewname, args=[self.system_mail.id, self.booking.id]),
            {
                'sender': self.address.id,
                'to': self.booking.customer.email,
                'subject': '件名',
                'content': '内容',
            }
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/send_confirm.html')
        self.assertEqual(list(res.context['object'].keys()), ['sender', 'to', 'subject', 'content'])


class TestSendTestMailView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'mail:テストメール送信'
        self.system_mail = SystemMail.objects.get(name='顧客登録完了メール')

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[self.system_mail.id]))
        self.assertTemplateUsed(res, 'mail/send_confirm.html')
        self.assertEqual(res.context['object'], self.system_mail)
        self.assertTrue(res.context['is_test'])

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname, args=[self.system_mail.id]))


class TestSendMail(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'mail:メール送信'

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname))

    def test_send_mail(self):
        data = {
            'sender': 'from@example.com',
            'to': 'to@example.com',
            'subject': 'subject',
            'content': 'content',
        }
        res = self.client.post(reverse(self.viewname), data)
        self.assertEqual(res.content.decode('utf-8'), '{"msg": "メールを送信しました。"}')
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.from_email, 'from@example.com')
        self.assertEqual(list(m.to), ['to@example.com'])
        self.assertEqual(m.subject, 'subject')
        self.assertEqual(m.body, 'content')

    @patch('yoyaku.mail.views.send_mail', return_value=0)
    def test_send_mail_failed(self, send_mail):
        data = {
            'sender': 'from@example.com',
            'to': 'to@example.com',
            'subject': 'subject',
            'content': 'content',
        }
        res = self.client.post(reverse(self.viewname), data)
        self.assertEqual(res.content.decode('utf-8'), '{"msg": "メールを送信できませんでした。"}')
        self.assertEqual(len(mail.outbox), 0)


class TestMailAddressListView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'mail:メールアドレス一覧'

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/mailaddress_list.html')

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname))


class TestAddressCreateView(AuthViewTestCase):
    def setUp(self):
        self.login()
        self.viewname = 'mail:メールアドレス登録'

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/mailaddress_form.html')
        self.assertTrue(isinstance(res.context['form'], AddressCreateUpdateForm))

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname))

    def test_post_success(self):
        res = self.client.post(reverse(self.viewname), {'email': 'test@example.com', 'memo': ''})
        self.assertRedirects(res, reverse('mail:メールアドレス一覧'))
        self.assertEqual(MailAddress.objects.filter(email='test@example.com').count(), 1)

    def test_post_failed(self):
        res = self.client.post(reverse(self.viewname), {'email': 'invalid'})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/mailaddress_form.html')

    def test_non_field_errors_is_added(self):
        res = self.client.post(reverse(self.viewname), {'email': 'invalid'})
        self.assertTrue(res.context['form'].non_field_errors())


class TestAddressUpdateView(AuthViewTestCase):
    def setUp(self):
        self.login()
        self.address = MailAddressFactory()
        self.viewname = 'mail:メールアドレス編集'

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[self.address.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/mailaddress_form.html')
        self.assertTrue(isinstance(res.context['form'], AddressCreateUpdateForm))

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname, args=[self.address.id]))

    def test_post_success(self):
        res = self.client.post(reverse(self.viewname, args=[self.address.id]), {'email': 'aaa@example.com'})
        self.assertRedirects(res, reverse('mail:メールアドレス一覧'))
        self.address.refresh_from_db()
        self.assertEqual(self.address.email, 'aaa@example.com')

    def test_post_fail(self):
        res = self.client.post(reverse(self.viewname, args=[self.address.id]), {'email': 'hoge'})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mail/mailaddress_form.html')

    def test_non_field_errors_is_added(self):
        res = self.client.post(reverse(self.viewname, args=[self.address.id]), {'email': 'hoge'})
        self.assertTrue(res.context['form'].non_field_errors())


class TestMailAddressDeleteView(AuthViewTestCase):
    def setUp(self):
        self.login()
        self.address = MailAddressFactory()
        self.viewname = 'mail:メールアドレス削除'
        self.success_url = reverse('mail:メールアドレス一覧')

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname, args=[self.address.id]))

    def test_post_success(self):
        res = self.client.post(reverse(self.viewname, args=[self.address.id]))
        self.assertRedirects(res, self.success_url)
        with self.assertRaises(MailAddress.DoesNotExist):
            self.address.refresh_from_db()

    def test_cannot_delete_used_address(self):
        SystemMailFactory(sender=self.address)
        res = self.client.post(reverse(self.viewname, args=[self.address.id]))
        self.assertRedirects(res, self.success_url)
        self.assertEqual(MailAddress.objects.filter(id=self.address.id).count(), 1)

    def test_delete_invalid_address(self):
        """削除済みのpkや登録されていないpkを指定した時"""
        res = self.client.post(reverse(self.viewname, args=[0]))
        self.assertRedirects(res, self.success_url)
