from django.test import TestCase
from django.utils.timezone import localtime

from yoyaku.accounts.models import Ages
from yoyaku.accounts.excel_export_service import get_customers_xl
from yoyaku.tests.factories import BookingFactory, CustomerFactory, StaffFactory, SuperUserFactory


class TestExcelExportService(TestCase):

    fixtures = ['accounts']

    def setUp(self):
        self.superuser = SuperUserFactory()
        self.staff = StaffFactory()
        self.customer = CustomerFactory(
            user_id='田中',
            username='田中',
            furigana='タナカ',
            email='tanaka@example.com',
            phone_number='08012345678',
            linename='tanaka',
            age=20,
            ages=Ages.objects.get(id=2),
            job='プログラマー',
            zip_code='0001111',
            zip='Tokyo',
            workable_time='9:00~10:00',
            side_business_experience='はい',
            contact='コンタクト',
            memo1='メモ1',
            memo2='メモ2',
        )
        self.booking = BookingFactory(customer=self.customer, staff=self.staff)

    def test_get_customers_xl(self):
        header = ['顧客id', 'スタッフ', '名前', 'フリガナ', 'メールアドレス', '電話番号', 'LINE名', '年齢', '年代',
                  '職業', '郵便番号', '住所', '作業可能時間', '副業経験', 'お問い合わせ内容', 'メモ1',
                  'メモ2', '削除フラグ', '作成日時']
        output_fields = ['id', 'staff', 'username', 'furigana', 'email', 'phone_number', 'linename', 'age', 'ages', 'job',
                         'zip_code', 'zip', 'workable_time', 'side_business_experience', 'contact', 'memo1', 'memo2',
                         'is_active', 'date_joined']
        wb = get_customers_xl()
        ws = wb.active
        self.assertEqual(ws.title, '顧客データ')

        # check header 1行目
        for c, value in enumerate(header, 1):
            self.assertEqual(ws.cell(row=1, column=c).value, header[c-1])

        # check customers data 2行目
        for c, field in enumerate(output_fields, 1):
            if field == 'staff':
                self.assertEqual(ws.cell(row=2, column=c).value, self.booking.get_staff_name())
            elif field == 'date_joined':
                value = localtime(getattr(self.customer, field))
                value = value.strftime('%Y-%m-%d %H:%M')
                self.assertEqual(ws.cell(row=2, column=c).value, value)
            elif field == 'ages':
                self.assertEqual(ws.cell(row=2, column=c).value, str(getattr(self.customer, field)))
            else:
                self.assertEqual(ws.cell(row=2, column=c).value, getattr(self.customer, field))

        # customerは1人のため、３行目にデータはない
        for c, field in enumerate(output_fields, 1):
            self.assertIsNone(ws.cell(row=3, column=c).value)
