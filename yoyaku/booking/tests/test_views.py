from datetime import timezone

from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import utc

from yoyaku.booking.forms import *
from yoyaku.booking.models import Booking, BookingLimit
from yoyaku.booking.utils import get_today0000
from yoyaku.tests.factories import BookingFactory, BookingLimitFactory, CustomerFactory, StaffFactory
from yoyaku.tests.test_case import AuthViewTestCase


class TestBookingLimitListView(AuthViewTestCase):
    def setUp(self):
        self.login()
        self.viewname = 'booking:予約枠一覧'

    def test_get(self):
        """初回表示 ページ数指定なし"""
        res = self.client.get(reverse(self.viewname))
        day_list_expected = [(get_today0000() + timedelta(days=i))
                             for i in range(settings.DISP_DAYS)]

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['day_list'], day_list_expected)
        self.assertEqual(res.context['start'], get_today0000())
        self.assertEqual(res.context['page_no'], 0)
        self.assertTemplateUsed(res, 'booking/booking_limit_list.html')

    def test_get_with_page(self):
        for page in [-2, -1, 0, 1, 2]:
            res = self.client.get(reverse(self.viewname), {'page': page})
            start = get_today0000() + timedelta(days=page * settings.DISP_DAYS)
            day_list_expected = [(start + timedelta(days=i))
                                 for i in range(settings.DISP_DAYS)]

            with self.subTest(page=page):
                self.assertEqual(res.context['day_list'], day_list_expected)
                self.assertEqual(res.context['start'], start)
                self.assertEqual(res.context['page_no'], page)

    def test_page_overflow(self):
        for page in (-1000000000, 1000000000):
            res = self.client.get(reverse(self.viewname), {'page': page})
            with self.subTest(page=page):
                self.assertEqual(res.status_code, 404)

    def test_post_create_multiple_booking_limit(self):
        res = self.client.post(
            reverse(self.viewname),
            {
                'start_datetime': '2000-01-01',
                'end_datetime': '2000-01-02',
                'time0900': True,
                'time0930': True,
                'limit': 3,
            },
        )
        self.assertRedirects(res, reverse('booking:予約枠一覧'))
        self.assertEqual(BookingLimit.objects.count(), 4)

    def test_post_form_error(self):
        res = self.client.post(
            reverse(self.viewname),
            {
                'start_datetime': '2000-01-01',
                'end_datetime': '2000-01-01',
                'time0900': True,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'booking/booking_limit_list.html')
        self.assertEqual(len(res.context['form'].errors), 1)


class TestBookingListView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.set_bookings()
        self.viewname = 'booking:予約一覧'

    def set_bookings(self):
        # 2日前~4日後 (計7個) の予約枠を作成する
        for i in range(-2, 5):
            BookingLimitFactory(limit=20, start_datetime=get_today0000() + timedelta(days=i, hours=9))
        bl_list = BookingLimit.objects.all().order_by('start_datetime')

        # 予約を14個作成 その内半分はstaff割り当てる。上で作成した予約枠を均等に割り当てる
        for i in range(14):
            staff = None if i % 2 else self.staff
            BookingFactory(
                staff=staff,
                booking_limit=bl_list[int(i / 2)],
            )

    def test_get_if_booking_zero(self):
        """予約0件時のテスト"""
        BookingLimit.objects.all().delete()
        res = self.client.get(reverse(self.viewname))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['staff_form_list'], [])
        self.assertEqual(res.context['where_str'], '')
        self.assertTemplateUsed(res, 'booking/booking_list.html')

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_get(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['paginator'].count, 10)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_page_size(self):
        for page_size in settings.PER_PAGE_SET:
            with self.subTest(page_size=page_size):
                res = self.client.get(reverse(self.viewname), {'page_size': page_size})
                self.assertEqual(len(res.context['page_obj'].object_list), page_size)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_invalid_page_size(self):
        for page_size in [-1, 0, 22]:
            with self.subTest(page_size=page_size):
                res = self.client.get(reverse(self.viewname), {'page_size': page_size})
                self.assertEqual(len(res.context['page_obj'].object_list), settings.PER_PAGE_SET[0])

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_search_from_datetime_or_to_datetime(self):
        """pageやpage_size指定のリンクにクエリ文字列が使われている"""
        params = [
            ('from_datetime', (get_today0000() - timedelta(days=3)).strftime('%Y-%m-%d'), 14),
            ('from_datetime', (get_today0000() - timedelta(days=2)).strftime('%Y-%m-%d'), 14),
            ('to_datetime', get_today0000().strftime('%Y-%m-%d'), 6),
            ('to_datetime', (get_today0000() + timedelta(days=3)).strftime('%Y-%m-%d'), 12),
            ('to_datetime', (get_today0000() + timedelta(days=4)).strftime('%Y-%m-%d'), 14),
        ]
        for key, value, expected in params:
            with self.subTest(key=key, value=value, expected=expected):
                res = self.client.post(reverse(self.viewname), {key: value})
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.context['paginator'].count, expected)

                # テンプレートに&を描画する時、&amp;に置換される
                query_str = f'?page=1&page_size={settings.PER_PAGE_SET[0]}&amp;{key}={value}'
                self.assertContains(res, query_str)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_search_staff(self):
        key = 'staff'
        value = self.staff.id
        excepted = 7
        res = self.client.post(reverse(self.viewname), {key: value})
        self.assertEqual(res.context['paginator'].count, excepted)

        # テンプレートに&を描画する時、&amp;に置換される
        query_str = f'?page=1&page_size={settings.PER_PAGE_SET[0]}&amp;{key}={value}'
        self.assertContains(res, query_str)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_search_unknown(self):
        key = 'unknown'
        value = 'true'
        excepted = 7

        res = self.client.post(reverse(self.viewname), {key: value})
        self.assertEqual(res.context['paginator'].count, excepted)

        # テンプレートに&を描画する時、&amp;に置換される
        query_str = f'?page=1&page_size={settings.PER_PAGE_SET[0]}&amp;{key}={value}'
        self.assertContains(res, query_str)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_querystr_from_to(self):
        params = [
            ('from_datetime', (get_today0000() - timedelta(days=2)).strftime('%Y-%m-%d'), 14),
            ('to_datetime', get_today0000().strftime('%Y-%m-%d'), 6),
        ]
        for key, value, expected in params:
            with self.subTest(key=key, value=value, expected=expected):
                res = self.client.post(reverse(self.viewname), {'page': 1, 'page_size': {settings.PER_PAGE_SET[0]}, key: value})
                self.assertEqual(res.context['paginator'].count, expected)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_querystr_staff(self):
        value = self.staff.id
        res = self.client.get(reverse(self.viewname), {'page': 1, 'page_size': {settings.PER_PAGE_SET[0]}, 'staff': value})
        self.assertEqual(res.context['paginator'].count, 7)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_querystr_unknown(self):
        res = self.client.get(reverse(self.viewname), {'page': 1, 'page_size': {settings.PER_PAGE_SET[0]}, 'unknown': 'true'})
        self.assertEqual(res.context['paginator'].count, 7)


class TestBookingCreateView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.customer = CustomerFactory()
        self.user = StaffFactory()
        self.bl = BookingLimitFactory(limit=1, start_datetime=get_today0000() + timedelta(days=10))
        self.viewname = 'booking:予約登録'

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[self.customer.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'booking/booking_form.html')
        self.assertEqual(res.context['customer'], self.customer)

    def test_get_not_exist_customer_id(self):
        res = self.client.get(reverse(self.viewname, args=[0]))
        self.assertEqual(res.status_code, 404)

    def test_post_by_selected_bookinglimit_list(self):
        """登録後 顧客一覧にリダイレクト"""
        res = self.client.post(
            reverse(self.viewname, args=[self.customer.id]),
            {
                'staff': self.user.id,
                'customer': self.customer.id,
                'start_datetime': '2021-07-02T09:00:00+09:00',
                'select_booking_limit': True,
                'booking_limit': self.bl.id,
            },
        )
        self.assertRedirects(res, reverse('accounts:顧客詳細', args=[self.customer.id]))
        self.assertEqual(Booking.objects.count(), 1)

    def test_post_selected_calender(self):
        res = self.client.post(
            reverse(self.viewname, args=[self.customer.id]),
            {
                'staff': self.user.id,
                'customer': self.customer.id,
                'start_datetime': '3000-07-02T10:00:00+09:00',
                'select_booking_limit': False,
            },
        )
        
        self.assertRedirects(res, reverse('accounts:顧客詳細', args=[self.customer.id]))
        self.assertEqual(Booking.objects.count(), 1)

    def test_form_invalid_add_non_field_errors(self):
        res = self.client.post(reverse(self.viewname, args=[self.customer.id]))
        self.assertTrue(res.context['form'].non_field_errors())


class TestBookingUpdateView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.viewname = 'booking:予約変更'
        self.viewname2 = 'booking:予約変更_顧客詳細'
        self.bl = BookingLimitFactory(limit=1, start_datetime=get_today0000() + timedelta(days=1))
        self.booking = BookingFactory(booking_limit=self.bl)

    def test_get(self):
        res = self.client.get(reverse(self.viewname, args=[self.booking.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'booking/booking_form.html')

    def test_post_select_booking_limit(self):
        res = self.client.post(
            reverse(self.viewname, args=[self.booking.id]),
            {
                'staff': self.staff.id,
                'customer': self.booking.customer.id,
                'start_datetime': '2021-07-02T10:00:00+09:00',
                'select_booking_limit': True,
                'booking_limit': self.booking.booking_limit.id,
            },
        )
        self.booking.refresh_from_db()
        self.assertRedirects(res, reverse('booking:予約一覧'))
        self.assertEqual(self.booking.staff.id, self.staff.id)

    def test_post_redirect_to_customer_detail(self):
        """self.viewname2からのpostの場合、顧客詳細にリダイレクト"""
        res = self.client.post(
            reverse(self.viewname2, args=[self.booking.id]),
            {
                'staff': self.staff.id,
                'customer': self.booking.customer.id,
                'start_datetime': '2021-07-02T10:00:00+09:00',
                'select_booking_limit': False,
                'booking_limit': self.booking.booking_limit.id,
            },
        )
        self.assertRedirects(res, reverse('accounts:顧客詳細', args=[self.booking.customer.id]))

    def test_form_error(self):
        """フォームエラーが発生する場合 不明なユーザを選択"""
        res = self.client.post(
            reverse(self.viewname, args=[self.booking.id]),
            {
                'staff': 11,
                'customer': self.booking.customer.id,
                'start_datetime': '2021-07-02T10:00:00+09:00',
                'select_booking_limit': True,
                'booking_limit': 0,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['form'].errors['staff'], ['正しく選択してください。選択したものは候補にありません。'])
        self.assertEqual(res.context['form'].errors['booking_limit'], ['選択した予約枠は既に満員か、リストに存在しません。'])
        self.assertTrue(res.context['form'].non_field_errors())
        self.assertTemplateUsed(res, 'booking/booking_form.html')

    def test_form_invalid_add_non_field_errors(self):
        res = self.client.post(reverse(self.viewname, args=[self.booking.id]))
        self.assertTrue(res.context['form'].non_field_errors())


class TestUpdateBookingUserView(AuthViewTestCase):

    def setUp(self):
        self.login()
        bl = BookingLimitFactory(limit=1, start_datetime=datetime(2020, 1, 1, tzinfo=utc))
        self.booking = BookingFactory(booking_limit=bl)
        self.viewname = 'booking:予約担当変更'

    def test_post(self):
        res = self.client.post(
            reverse(self.viewname),
            {
                'staff_id': self.staff.id,
                'booking_id': self.booking.id,
                'requested_at': datetime.now(),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.booking.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.decode('utf-8'), '{"msg": "スタッフを更新しました。"}')
        self.assertEqual(self.booking.staff.id, self.staff.id)
        self.assertEqual(self.booking.updated_by, self.staff)

    def test_is_not_ajax_error(self):
        res = self.client.post(reverse(self.viewname), {})
        self.assertEqual(res.status_code, 404)

    def test_get_not_allowed(self):
        res = self.client.get(reverse(self.viewname))
        self.assertEqual(res.status_code, 405)

    def test_staff_is_not_active(self):
        """ユーザ削除済の場合リロードメッセージを返す"""
        not_active_staff = StaffFactory(is_active=False)
        res = self.client.post(
            reverse(self.viewname),
            {
                'staff_id': not_active_staff.id,
                'booking_id': self.booking.id,
                'requested_at': datetime.now(),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.decode('utf-8'), '{"msg": "reload"}')

    def test_booking_does_not_exist(self):
        """
        予約削除済(データが存在しない)の場合
        """
        res = self.client.post(
            reverse(self.viewname),
            {
                'staff_id': self.booking.staff.id,
                'booking_id': 11,
                'requested_at': datetime.now(),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res.content.decode('utf-8'), '{"msg": "reload"}')

    def test_updated_by_others(self):
        requested_at = datetime.now(tz=timezone.utc)
        staff_sub = StaffFactory()
        self.booking.updated_by = staff_sub
        self.booking.updated_at = datetime.now(tz=timezone.utc)
        self.booking.save()
        res = self.client.post(
            reverse(self.viewname),
            {
                'staff_id': self.booking.staff.id,
                'booking_id': self.booking.id,
                'requested_at': requested_at,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res.content.decode('utf-8'), '{"msg": "reload"}')


class TestBookingDeleteView(AuthViewTestCase):

    def setUp(self):
        self.login()
        self.booking = BookingFactory()
        self.viewname = 'booking:予約削除'

    def test_get_not_allowed(self):
        self.login()
        res = self.client.get(reverse(self.viewname, args=[1]))
        self.assertEqual(res.status_code, 405)

    def test_post(self):
        res = self.client.post(reverse(self.viewname, args=[self.booking.id]))
        self.assertRedirects(res, reverse('accounts:顧客詳細', args=[self.booking.customer.id]))
        self.assertEqual(Booking.objects.filter(id=self.booking.id).count(), 0)

    def test_delete_invalid_booking(self):
        res = self.client.post(reverse(self.viewname, args=[0]))
        self.assertRedirects(res, reverse('accounts:顧客一覧'))
