import copy
import re
from datetime import datetime, time, timedelta

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware, now

from yoyaku.accounts.models import User
from yoyaku.booking.models import Booking, BookingLimit
from yoyaku.booking.utils import date_range, get_today0000, is_valid_booking_time, get_time_frames, get_start_times


def copy_boolean_field(copied, label):
    """
    copied引数を複製し、ラベルを変更したオブジェクトを返す。
    copied : BooleanField
    label : str 
    """
    result = copy.deepcopy(copied)
    result.label = label
    return result


class BookingLimitEditForm(forms.ModelForm):
    # 画面側でチェックを入れると全てのtimeにチェックされるため、clean()やsave()では利用しない
    time_all = forms.BooleanField(
        label='全て',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control'}),
    )

    end_datetime = forms.DateField(
        label='終了日',
        widget=forms.DateInput(attrs={'class': 'form-control datetimepicker'})
    )

    class Meta:
        model = BookingLimit
        fields = ('limit', 'start_datetime')
        widgets = {'limit': forms.NumberInput(attrs={'class': 'form-control'})}
        field_classes = {'start_datetime': forms.DateField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_datetime'].label = '開始日'
        self.fields['start_datetime'].widget = forms.DateInput(attrs={'class': 'form-control datetimepicker'})

        # 時間帯のチェックボックスを生成
        start_times = get_start_times()
        time_frames = get_time_frames()
        for i, start_time in enumerate(start_times):
            field_name = f'time{start_time}'.replace(':', '')
            self.fields[field_name] = copy_boolean_field(self.fields['time_all'], time_frames[i])

    def clean_start_datetime(self):
        """dateからdatetimeに変換する"""
        d = self.cleaned_data['start_datetime']
        return make_aware(datetime(d.year, d.month, d.day))

    def clean_end_datetime(self):
        """dateからdatetimeに変換する"""
        d = self.cleaned_data['end_datetime']
        return make_aware(datetime(d.year, d.month, d.day))

    def clean(self):
        data = super().clean()
        if 'start_datetime' not in data or 'end_datetime' not in data:
            return

        if data['end_datetime'] < data['start_datetime']:
            self.add_error('start_datetime', ValidationError('開始日は終了日より前にしてください。', code='out_of_date'))
            return

        start_dt_list = [start_dt for start_dt in self.iterate_checked_frame(data)]
        bl_list = BookingLimit.objects.prefetch_related('bookings').filter(start_datetime__in=start_dt_list)
        for bl in bl_list:
            if data['limit'] < bl.bookings.count():
                raise ValidationError(
                    '開始日時%(value)sの枠数が予約数を下回っていたため変更できませんでした。',
                    params={'value': bl.start_datetime.strftime('%Y-%m-%d %H:%M')},
                    code='booking_overflow',
                )

    def save(self, commit=True):
        """
        入力した期間とチェックした時間全てに設定した予約枠数のデータを作成する
        予約枠が存在する日時は枠数を更新する
        """
        data = self.cleaned_data
        # 作成・更新する日時のリストを作成
        start_dt_list = [start_dt for start_dt in self.iterate_checked_frame(data)]
        # 更新対象を抽出
        update_bl_list = BookingLimit.objects.filter(start_datetime__in=start_dt_list)

        # 更新対象の予約枠数の変更と、作成対象を抽出
        for bl in update_bl_list:
            bl.limit = data['limit']
            start_dt_list.remove(bl.start_datetime)

        create_bl_list = [
            BookingLimit(limit=data['limit'], start_datetime=dt)
            for dt in start_dt_list
        ]
        BookingLimit.objects.bulk_update(update_bl_list, fields=['limit'])
        BookingLimit.objects.bulk_create(create_bl_list)

    def iterate_checked_frame(self, data):
        """
        変更期間内のチェックされている日時のデータを返すイテレーター
        data: フォームで入力されたデータ
        """
        checked_time_list = []
        for key in data:
            m = re.match(r'time(\d{4})', key)
            if m and data[key]:
                time_str = m.groups()[0]
                checked_time_list.append(time(int(time_str[:2]), int(time_str[2:])))

        for d in date_range(data['start_datetime'], data['end_datetime']):
            for t in checked_time_list:
                yield make_aware(datetime.combine(d, t))


class BookingSearchForm(forms.Form):
    """予約検索用フォーム"""
    staff = forms.ModelChoiceField(
        required=False,
        queryset=User.staffs.is_active(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='',
    )
    unknown = forms.BooleanField(
        label='未定義',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-control', 'value': 'true'}),
    )
    from_datetime = forms.CharField(
        label='開始日',
        required=False,
        max_length=32,
        widget=forms.TextInput(attrs={'class': 'form-control datetimepicker'})
    )
    to_datetime = forms.CharField(
        label='終了日',
        required=False,
        max_length=32,
        widget=forms.TextInput(attrs={'class': 'form-control datetimepicker'})
    )

    def clean_from_datetime(self):
        """開始日が指定されている場合は開始時間とタイムゾーンを付与する"""
        from_datetime = self.cleaned_data['from_datetime']
        if from_datetime:
            return make_aware(datetime.strptime(from_datetime, '%Y-%m-%d'))
        return None

    def clean_to_datetime(self):
        """
        終了日が指定されている場合はタイムゾーン付きのdatetime型に変換する
        filter用に +1日する
        """
        to_datetime = self.cleaned_data['to_datetime']
        if to_datetime:
            return make_aware(datetime.strptime(to_datetime, '%Y-%m-%d')) + timedelta(days=1)
        return None

    def get_where(self):
        """
        フォームに入力された検索条件を元にBookingモデルのフィルターを作成する。
        検索フォームが未入力の場合は、当日以降の予約をフィルターの条件とする。
        """
        where = {
            'booking_limit__start_datetime__gte': self.cleaned_data.get('from_datetime'),
            'booking_limit__start_datetime__lt': self.cleaned_data.get('to_datetime'),
            'staff': self.cleaned_data.get('staff'),
        }
        where = {k: v for k, v in where.items() if v}
        # 未定義がチェックされている場合
        if self.cleaned_data.get('unknown'):
            where['staff_id'] = None

        # 検索条件が何もなかったらデフォルトの検索条件に設定
        if not len(where):
            where = {
                'booking_limit__start_datetime__gte': get_today0000().isoformat(' '),
            }
        return where

    def get_info(self, booking_count):
        """開始日と終了日を指定して検索した場合に表示する統計情報を取得する"""

        result = ''

        if 'cleaned_data' not in self.__dict__:
            return result

        from_datetime = self.cleaned_data.get('from_datetime')
        to_dateitme = self.cleaned_data.get('to_datetime')
        if not from_datetime or not to_dateitme:
            return result

        limit_total = sum(
            BookingLimit.objects
            .filter(start_datetime__gte=from_datetime, start_datetime__lt=to_dateitme)
            .values_list('limit', flat=True)
        )

        to_dateitme -= timedelta(days=1)  # filter用に1日増加した分を減らす
        result += f"{from_datetime.strftime('%Y-%m-%d')} ~ {to_dateitme.strftime('%Y-%m-%d')}"

        staff = self.cleaned_data.get('staff')
        unknown = self.cleaned_data.get('unknown')
        if staff and unknown:
            result += f' {staff.username}, 未定義'
        elif staff:
            result += f' {staff.username}'
        elif unknown:
            result += ' 未定義'

        result += f' 予約総数 / 予約枠総数 = {booking_count} / {limit_total}'
        return result


class BookingForm(forms.ModelForm):

    select_booking_limit = forms.BooleanField(
        label='予約枠から選ぶ',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    start_datetime = forms.DateTimeField(
        label='開始日時',
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'placeholder': '2000-01-01 10:00'}),
    )

    class Meta:
        model = Booking
        fields = ('staff', 'customer', 'booking_limit')
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.HiddenInput(),
            'booking_limit': forms.Select(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'booking_limit': {
                'invalid_choice': '選択した予約枠は既に満員か、リストに存在しません。',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['booking_limit'].queryset = BookingLimit.objects.can_book(self.instance.booking_limit)
        else:
            self.fields['booking_limit'].queryset = BookingLimit.objects.can_book()
        self.fields['booking_limit'].empty_label = None
        self.fields['booking_limit'].required = False
        self.fields['staff'].queryset = User.staffs.is_active()
        self.fields['staff'].empty_label = ''

    def add_booking_filled_error(self, start_datetime):
        self.add_error(
            'start_datetime',
            ValidationError(
                '%(value)sからの予約枠は満員です。',
                params={'value': start_datetime.strftime('%Y-%m-%d %H:%M')},
                code='booking_filled',
            ),
        )

    def clean(self):
        """
        リストから予約枠を選んだ場合は何もしない。
        カレンダーから予約日時を選んだ場合は妥当性をチェック
        """
        cleaned_data = super().clean()

        # リストから指定
        if cleaned_data.get('select_booking_limit'):
            return

        # カレンダーから指定
        start_datetime = cleaned_data.get('start_datetime')
        if start_datetime:
            if not is_valid_booking_time(start_datetime):
                self.add_error(
                    'start_datetime',
                    ValidationError(
                        '開始時間は%(from)s~%(to)sまでの30分区切りにしてください。',
                        params={
                            'from': settings.START_TIME,
                            'to': settings.END_TIME,
                        },
                        code='booking_time',
                    )
                )
                return
            # 予約枠がある場合は満席かチェックをする
            bl_list = BookingLimit.objects.prefetch_related('bookings').filter(start_datetime=start_datetime)
            if bl_list.exists() and self._is_filled(bl_list[0]):
                self.add_booking_filled_error(start_datetime)

    def _is_filled(self, booking_limit):
        if self.instance.id:
            return booking_limit.is_filled(exclude=self.instance)
        return booking_limit.is_filled()

    def save(self, updated_by):
        """customer: 新規作成時に指定する必要がある"""
        obj = super().save(commit=False)
        is_checked = self.cleaned_data['select_booking_limit']
        if is_checked:
            obj.booking_limit = self.cleaned_data['booking_limit']
        else:
            # カレンダーから指定した予約枠がない場合、BookingLimitを作成する
            bl, created = BookingLimit.objects.get_or_create(
                start_datetime=self.cleaned_data['start_datetime'],
                defaults={'limit': 1},
            )
            obj.booking_limit = bl

        obj.updated_by = updated_by
        obj.save()
        return obj


class UpdateStaffForm(forms.Form):
    """スタッフを更新するためのフォーム"""
    staff = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control select-staff'}),
    )

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 選択肢をセットする
        self.fields['staff'].choices = choices


class RegisterBookingForm(forms.Form):
    """LPページで予約日時を設定するためのフォーム"""
    booking_limit = forms.IntegerField(
        widget=forms.HiddenInput(
            attrs={
                'class': 'no_time selected_id',
                'data-border-color': '',
                'data-background-color': ''
            }
        ),
        error_messages={
            'required': '希望日時は必須です。カレンダーからご希望の日時を選択してください。',
        },
    )

    def clean_booking_limit(self):

        booking_limit_id = self.cleaned_data['booking_limit']

        try:
            bl = BookingLimit.objects.select_for_update().get(id=booking_limit_id)
        except BookingLimit.DoesNotExist:
            raise ValidationError('予約枠を確保できませんでした。他の予約枠を選択してください。', code='invalid_choice')

        if bl.is_filled():
            raise ValidationError(
                'ご希望の予約日時は満席になりました。他の日時を選択してください。',
                code='filled',
            )
        elif bl.start_datetime < now()+timedelta(minutes=60):
            raise ValidationError(
                '予約日時が現在時刻より１時間未満のため予約できませんでした。他の希望日時を選択してください。',
                code='out_of_date',
            )

        return booking_limit_id

    def save(self, customer):
        bl = BookingLimit.objects.get(id=self.cleaned_data['booking_limit'])
        return Booking.objects.create(booking_limit=bl, customer=customer)
