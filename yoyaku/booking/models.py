from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from yoyaku.accounts.models import User


class BookingLimitManager(models.Manager):
    use_in_migrations = True

    def can_book(self, include=None):
        """
        予約可能な予約枠のリストを取得する。
        現在時刻以降の予約枠が空いている予約枠のリストを取得する
        """
        start = timezone.now()
        where = {'start_datetime__gte': start}

        bl_list = self.prefetch_related('bookings').filter(**where).order_by('start_datetime')
        possible_ids = {bl.id for bl in bl_list if not bl.is_filled()}
        if include:
            possible_ids.add(include.id)
        return bl_list.filter(id__in=possible_ids)

    def customers_can_select(self, after_min):
        """
        現在時刻から'after_min'分後以降の予約枠リストと状態を返す。満員含む。
        """
        start_datetime = timezone.now() + timezone.timedelta(minutes=after_min)
        where = {'start_datetime__gte': start_datetime}
        bl_list = self.prefetch_related('bookings').filter(**where).order_by('start_datetime')
        return bl_list


class BookingLimit(models.Model):
    """予約枠のモデル"""
    limit = models.PositiveIntegerField(_('予約枠数'))
    start_datetime = models.DateTimeField(_('開始日時'), unique=True)
    end_datetime = models.DateTimeField(_('終了日時'), null=True, blank=True)
    created_at = models.DateTimeField(_('作成日時'), default=timezone.now)

    objects = BookingLimitManager()

    def formatted_start_datetime(self):
        format = '%Y年%m月%d日 %H時%M分'
        localized_dt = timezone.localtime(self.start_datetime)
        return localized_dt.strftime(format)

    def __str__(self):
        """予約枠と予約状況の説明を返す。"""
        localized_dt = timezone.localtime(self.start_datetime)
        datetime_str = localized_dt.strftime('%Y-%m-%d %H:%M')
        return f'開始日時：{datetime_str} 予約状況：{self.booked_count} / {self.limit}'

    def __repr__(self):
        return f'id={self.id}, 予約枠数={self.limit}, 開始日時={self.start_datetime}'

    def is_filled(self, exclude=None):
        """
        満員ならTrue、空ありならFalse
        exclude: 予約数から除外するBookingオブジェクト。
        予約の更新時に予約に紐付くBookingLimitが満員でもエラーにしない様にしている。
        """
        if exclude:
            return self.limit <= self.bookings.exclude(id=exclude.id).count()

        return self.limit <= self.booked_count

    @property
    def booked_count(self):
        """予約数を返す"""
        return self.bookings.count()

    def get_state(self):
        """
        残りの枠数から状態（●、▲、×）を判定する
        残り0枠 ×
        3枠以下 残り1枠 ▲
        4or5枠 残り1枠以上2枠以下 ▲
        6枠以上 (予約数/枠数+0.005) < 0.3 ▲ 30%未満(端数は切り上げ)
        Returns:
            [string]: 状態
        """
        rest = self.limit - self.booked_count
        if rest == 0:
            return '×'
        elif self.limit <= 3 and rest <= 1:
            return '▲'
        elif self.limit in (4, 5) and rest <= 2:
            return '▲'
        elif 6 <= self.limit and (rest / self.limit + 0.005) < 0.3:
            return '▲'
        else:
            return '●'


class Booking(models.Model):
    """
    予約のモデル
    """
    customer = models.OneToOneField(User, on_delete=models.CASCADE)
    booking_limit = models.ForeignKey(BookingLimit, on_delete=models.CASCADE, related_name='bookings')
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='booking_set')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_bookings')
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    created_at = models.DateTimeField(_('作成日時'), default=timezone.now)

    def __repr__(self):
        return f'id={self.id}, 予約枠={self.booking_limit_id},顧客ID={self.customer_id} スタッフID={self.staff_id}'

    def get_staff_name(self):
        return self.staff.username if self.staff else '未定義'

    def get_start_datetime(self):
        return self.booking_limit.start_datetime

    def is_updated_by_others(self, dt, requestuser):
        """
        指定日時以降に別のユーザによって更新されたかどうか
        dt: 指定日時 datetime
        requestuser: 更新者 accounts.model.User

        return
        True: 別のユーザにより更新された
        False: 前回と同じ更新者、または指定日時以降誰も更新していない
        """
        if requestuser != self.updated_by and dt < self.updated_at:
            return True
        else:
            return False
