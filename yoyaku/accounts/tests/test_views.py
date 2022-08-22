import urllib.parse

import factory
from django.conf import settings
from django.test import override_settings
from django.urls import reverse, reverse_lazy

from yoyaku.accounts.models import User
from yoyaku.accounts.forms import StaffForm, CustomerForm, CustomerSearchForm
from yoyaku.booking.models import Booking
from yoyaku.tests.factories import StaffFactory, CustomerFactory, BookingFactory
from yoyaku.tests.test_case import AuthViewTestCase


class TestStaffListView(AuthViewTestCase):
    fixtures = ['accounts']

    def setUp(self):
        self.login()
        self.viewname = 'accounts:スタッフ一覧'

    def test_login_required(self):
        self.assert_login_required(reverse(self.viewname))

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['paginator'].count, User.staffs.count())
        self.assertEqual(res.context['object_list'][0]['user_id'], self.staff.user_id)
        self.assertTemplateUsed(res, 'accounts/staff_list.html')

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_page_size(self):
        # スタッフはself.staff+新規staff2人の計3人
        factory.create_batch(User, 2, FACTORY_CLASS=StaffFactory)
        for page_size in settings.PER_PAGE_SET:
            with self.subTest(page_size=page_size):
                res = self.client.get(reverse(self.viewname), {'page_size': page_size})
                self.assertEqual(len(res.context['page_obj'].object_list), page_size)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_invalid_page_size_is_cleaned(self):
        for page_size in [-1, 0, 11, 'a']:
            with self.subTest(page_size=page_size):
                res = self.client.get(reverse(self.viewname), {'page_size': page_size})
                self.assertEqual(len(res.context['page_obj'].object_list), settings.PER_PAGE_SET[0])


class TestStaffCreateView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'accounts:スタッフ登録'

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/staff_form.html')
        self.assertTrue(isinstance(res.context['form'], StaffForm))

    def test_post_success(self):
        res = self.client.post(
            reverse(self.viewname),
            {
                'user_id': 'test_user',
                'username': 'test_user',
                'password1': '6yhnmju7',
                'password2': '6yhnmju7',
            }
        )
        self.assertRedirects(res, reverse('accounts:スタッフ一覧'))
        self.assertEqual(User.staffs.filter(user_id='test_user').count(), 1)

    def test_post_invalid_data(self):
        res = self.client.post(
            reverse(self.viewname),
            {'user_id': 'あああ', 'username': 'test_user'},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/staff_form.html')

    def test_non_field_errors(self):
        res = self.client.post(reverse(self.viewname), {})
        self.assertTrue(res.context['form'].non_field_errors())


class TestStaffUpdateView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.staff2 = StaffFactory()
        self.viewname = 'accounts:スタッフ編集'

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[self.staff2.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/staff_form.html')
        self.assertTrue(isinstance(res.context['form'], StaffForm))

    def test_post_success(self):
        res = self.client.post(
            reverse(self.viewname, args=[self.staff2.id]),
            {
                'user_id': self.staff2.user_id,
                'username': 'testuser_update',
                'password1': '6yhnmju7',
                'password2': '6yhnmju7',
            },
        )
        self.staff2.refresh_from_db()
        self.assertRedirects(res, reverse('accounts:スタッフ一覧'))
        self.assertEqual(self.staff2.username, 'testuser_update')

    def test_update_self(self):
        """ログインユーザが自身の情報を更新した時のテスト"""
        res = self.client.post(
            reverse(self.viewname, args=[self.staff.id]),
            {
                'user_id': self.staff.user_id,
                'username': 'testuser_update',
                'password1': '6yhnmju7',
                'password2': '6yhnmju7',
            },
        )

        self.staff.refresh_from_db()
        self.assertRedirects(res, reverse('accounts:スタッフ一覧'))
        self.assertEqual(self.staff.username, 'testuser_update')

    def test_post_invalid_data(self):
        res = self.client.post(
            reverse(self.viewname, args=[self.staff2.id]),
            {
                'user_id': self.staff2.user_id,
                'username': '',
                'password1': '',
                'password2': '',
            }
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/staff_form.html')
        self.assertTrue(res.context['form'].errors)

    def test_non_field_errors(self):
        res = self.client.post(reverse(self.viewname, args=[self.staff2.id]), {})
        self.assertTrue(res.context['form'].non_field_errors())


class TestStaffDeleteView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.delete_stuff = StaffFactory()
        self.viewname = 'accounts:スタッフ削除'
        self.success_url = reverse_lazy('accounts:スタッフ一覧')

    def test_get_not_allowed(self):
        res = self.client.get(reverse(self.viewname, args=[self.delete_stuff.id]))
        self.assertEqual(res.status_code, 405)

    def test_delete(self):
        res = self.client.post(reverse(self.viewname, args=[self.delete_stuff.id]))
        self.delete_stuff.refresh_from_db()
        self.assertRedirects(res, self.success_url)
        self.assertFalse(self.delete_stuff.is_active)

    def test_cannot_delete_superuser(self):
        """superuserを指定された時は削除されない"""
        res = self.client.post(reverse(self.viewname, args=[self.superuser.id]))
        self.staff.refresh_from_db()
        self.assertRedirects(res, self.success_url)
        self.assertTrue(self.superuser.is_active)

    def test_delete_unknown_user(self):
        res = self.client.post(reverse(self.viewname, args=[0]))
        self.assertRedirects(res, self.success_url)


class TestCustomerListView(AuthViewTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.customer_list = factory.create_batch(User, 3, FACTORY_CLASS=CustomerFactory)
        return super().setUpTestData()

    def setUp(self):
        self.login()
        self.viewname = 'accounts:顧客一覧'

    def test_get(self):
        customer = self.customer_list[0]
        BookingFactory(customer=customer, staff=self.staff)
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['paginator'].count, 3)
        self.assertTemplateUsed(res, 'accounts/customer_list.html')
        self.assertTrue(isinstance(res.context['form'], CustomerSearchForm))

    def test_export_customer_list_is_displayed_in_superuser_view(self):
        """superuserは'顧客一覧エクスポート'が表示される"""
        self.login_superuser()
        res = self.client.get(reverse(self.viewname))
        self.assertContains(res, '顧客一覧エクスポート')

    def test_export_customer_list_is_displayed_in_staff_view(self):
        """superuser以外は表示されない"""
        res = self.client.get(reverse(self.viewname))
        self.assertNotContains(res, '顧客一覧エクスポート')

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_page_size(self):
        for page_size in settings.PER_PAGE_SET:
            with self.subTest(page_size=page_size):
                res = self.client.get(reverse(self.viewname), {'page_size': page_size})
                self.assertEqual(len(res.context['page_obj'].object_list), page_size)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_page_size_invalid(self):
        for page_size in [-1, 0, 11, 'a']:
            with self.subTest(page_size=page_size):
                res = self.client.get(reverse(self.viewname), {'page_size': page_size})
                self.assertEqual(len(res.context['page_obj'].object_list), settings.PER_PAGE_SET[0])

    @override_settings(PER_PAGE_SET=[2, 3, 4])
    def test_search_mono_param(self):
        """
        検索結果数
        検索後ページ番号やページ数のurlに検索パラメータが追加されている
        """
        params = [
            ('username', 'てすと'),
            ('furigana', 'テスト'),
            ('email', 'example.com'),
            ('phone_number', '000'),
        ]
        for key, value in params:
            with self.subTest(key=key, value=value):
                res = self.client.post(reverse(self.viewname), {key: value})
                # テンプレートに&を描画する時、&amp;に置換される
                query_str = f'page=1&page_size={settings.PER_PAGE_SET[0]}&amp;{key}={value}'
                self.assertContains(res, query_str)

    @override_settings(PER_PAGE_SET=[2, 3, 4])
    def test_get_with_filter_params(self):
        """
        検索用urlクエリ文字がある場合テスト
        get後もページ番号やページ数のurlに検索パラメータが追加されている
        """
        params = [
            ('username', 'てすと'),
            ('furigana', 'テスト'),
            ('email', 'example.com'),
            ('phone_number', '000'),
        ]
        for key, value in params:
            with self.subTest(key=key, value=value):
                res = self.client.get(
                    reverse(self.viewname),
                    {
                        'page': 1,
                        'page_size': settings.PER_PAGE_SET[0],
                        key: value,
                    }
                )

                # テンプレートに&を描画する時、&amp;に置換される
                query_str = f'page=1&page_size={settings.PER_PAGE_SET[0]}&amp;{key}={value}'
                self.assertContains(res, query_str)


class TestCustomerDetailView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.customer = CustomerFactory()
        self.viewname = 'accounts:顧客詳細'

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[self.customer.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/customer_detail.html')

    def test_get_not_active_customer(self):
        self.customer.is_active = False
        self.customer.save()
        res = self.client.get(reverse(self.viewname, args=[self.customer.id]))
        self.assertEqual(res.status_code, 404)


class TestCustomerCreateView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'accounts:顧客登録'

    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/customer_form.html')
        self.assertTrue(isinstance(res.context['form'], CustomerForm))

    def test_post(self):
        res = self.client.post(
            reverse(self.viewname),
            {
                'username': 'てすと',
                'email': 'update@example.com',
                'phone_number': '01234567890',
            },
        )
        self.assertRedirects(res, reverse('accounts:顧客一覧'))
        self.assertEqual(User.customers.filter(email='update@example.com').count(), 1)

    def test_post_failed(self):
        res = self.client.post(
            reverse(self.viewname),
            {
                'username': '',
                'email': '',
                'phone_number': '',
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/customer_form.html')
        self.assertTrue(res.context['form'].errors)

    def test_non_field_errors(self):
        res = self.client.post(reverse(self.viewname), {})
        self.assertTrue(res.context['form'].non_field_errors())


class TestCustomerUpdateView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.customer = CustomerFactory()
        self.viewname = 'accounts:顧客編集'

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[self.customer.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/customer_form.html')
        self.assertTrue(isinstance(res.context['form'], CustomerForm))

    def test_post(self):
        res = self.client.post(
            reverse(self.viewname, args=[self.customer.id]),
            {
                'username': 'ユーザー名更新',
                'furigana': 'テスト',
                'email': self.customer.email,
                'phone_number': self.customer.phone_number,
            },
        )
        self.customer.refresh_from_db()
        self.assertRedirects(res, reverse('accounts:顧客詳細', args=[self.customer.id]))
        self.assertEqual(self.customer.username, 'ユーザー名更新')

    def test_post_failed(self):
        res = self.client.post(
            reverse(self.viewname, args=[self.customer.id]),
            {
                'username': '',
                'email': '',
                'phone_number': '',
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'accounts/customer_form.html')
        self.assertTrue(res.context['form'].errors)

    def test_non_field_errors(self):
        res = self.client.post(reverse(self.viewname, args=[self.customer.id]), {})
        self.assertTrue(res.context['form'].non_field_errors())


class TestCustomerDeleteView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'accounts:顧客削除'

    def test_get_not_allowed(self):
        res = self.client.get(reverse(self.viewname, args=[1]))
        self.assertEqual(res.status_code, 405)

    def test_delete(self):
        """
        論理削除できているか。
        顧客が予約していた予約枠も削除されているか
        """
        booking = BookingFactory()
        customer = booking.customer
        res = self.client.post(reverse(self.viewname, args=[customer.id]))
        customer.refresh_from_db()

        self.assertRedirects(res, reverse('accounts:顧客一覧'))
        self.assertFalse(customer.is_active)
        with self.assertRaises(Booking.DoesNotExist):
            booking.refresh_from_db()

    def test_delete_not_exist_customer(self):
        res = self.client.post(reverse(self.viewname, args=[0]))
        self.assertRedirects(res, reverse('accounts:顧客一覧'))


class TestCustomerListDownload(AuthViewTestCase):
    def setUp(self):
        self.viewname = 'accounts:顧客一覧ダウンロード'

    def test_get_not_allowed(self):
        self.login_superuser()
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 405)

    def test_superuser_download(self):
        self.login_superuser()
        res = self.client.post(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers['Content-Type'], 'application/ms-excel')

        filename = '顧客一括データ.xls'
        quoted_filename = urllib.parse.quote(filename)
        self.assertEqual(
            res.headers['Content-Disposition'],
            f"attachment; filename='{quoted_filename}'; filename*=UTF-8''{quoted_filename}"
        )

    def test_staff_cant_download(self):
        self.login()
        res = self.client.post(reverse(self.viewname))
        self.assertEqual(res.status_code, 403)
