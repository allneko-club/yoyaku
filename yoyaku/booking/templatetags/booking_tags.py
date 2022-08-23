from django import template
from django.conf import settings
from django.utils.timezone import localtime

from yoyaku.booking.utils import get_start_times, get_time_frames

register = template.Library()


def _create_limit_index(start, limit_list):
    """
    日付と時間枠の行列を作成し、インデックスの値を予約数/予約枠にする
    予約枠が存在しないばあいや0の場合は値を空にする
    """
    # 予約枠の一覧を初期化
    limit_index = {t: [''] * settings.DISP_DAYS for t in get_start_times()}
    # 日毎の[予約数合計, 枠数合計]のリストを初期化
    totals = [[0, 0] for i in range(settings.DISP_DAYS)]
    # 予約枠数を行列に代入する
    for l in limit_list:
        local_datetime = localtime(l.start_datetime)
        day_index = (local_datetime - start).days
        time_index = local_datetime.time().isoformat(timespec='minutes')

        # 予約枠が1つ以上ある場合は予約数を検索し、予約数と枠数の結果を保存する。
        # totalsを更新する。
        if 0 < l.limit:
            count = l.bookings.count()
            limit_index[time_index][day_index] = [count, l.limit]
            totals[day_index][0] += count
            totals[day_index][1] += l.limit

    limit_index['total'] = totals

    return limit_index


@register.simple_tag
def create_rows(limit_list, start, *args, **kwargs):
    """
    予約枠の時間毎のデータと日毎の予約総数/枠総数をテーブルとして表示できるhtmlを生成する
    {% create_rows limit_list time_frames start as rows %}
        {{ rows|safe }}
    time_frames: 時間枠のリスト
    limit_index: 時間と日時の行列
    start: 開始日
    """
    limit_index = _create_limit_index(start, limit_list)
    time_frames = get_time_frames()

    tr_list = []
    for i, limit_lists in enumerate(limit_index.values()):
        tr = f'<td>{time_frames[i]}</td>'
        for l in limit_lists:
            if type(l) == list:
                tr += f'<td>{l[0]} / {l[1]}</td>'
            else:
                tr += '<td></td>'
        tr = f'<tr>{tr}</tr>'
        tr_list.append(tr)

    return ''.join(tr_list)
