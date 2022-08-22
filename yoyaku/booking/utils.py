from datetime import date, datetime, timedelta

from django.conf import settings
from django.utils.timezone import make_aware


def get_disp_hour_from():
    return int(settings.START_TIME.split(':')[0])


def get_disp_hour_to():
    return int(settings.END_TIME.split(':')[0])


def is_valid_booking_time(dt):
    """
    予約時間の時、分が妥当かどうか
    dt: datetime型
    """
    return is_valid_hour(dt) and is_valid_minute(dt)


def is_valid_hour(dt):
    """
    予約時間の時が妥当かどうか
    dt: datetime型
    """
    return get_disp_hour_from() <= dt.hour < get_disp_hour_to()


def is_valid_minute(dt):
    """予約時間の分が妥当かどうか"""
    return dt.minute in (0, 30)


def get_time_frames(total=True):
    """
    30分区切りの時間帯のリスト
    例）['9:00~9:30', '9:30~10:00', ~ '21:30~22:00', '合計']
    """
    result = []
    for i in range(get_disp_hour_from(), get_disp_hour_to()):
        result.extend([f'{i}:00~{i}:30', f'{i}:30~{i+1}:00'])

    if total:
        result.append('合計')

    return result


def get_start_times():
    """
    ゼロ埋めした開始時間のリスト
    例）['09:00', '09:30', '10:00', ~ '21:30']
    """
    result = []
    for i in range(get_disp_hour_from(), get_disp_hour_to()):
        result.extend([f'{i:02}:00', f'{i:02}:30'])

    return result


def date_range(start_date, end_date):
    """
    開始日〜終了日の日付を返す。
    start_date: datetime.date 開始日
    end_date: datetime.date 終了日
    return: datetime.date
    """
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(days=n)


def get_today0000():
    """今日の0時0分のdatetimeオブジェクトを取得"""
    today = date.today()
    return make_aware(datetime(today.year, today.month, today.day))
