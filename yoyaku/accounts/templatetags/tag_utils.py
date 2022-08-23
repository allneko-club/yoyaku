from django import template
from django.utils.timezone import now

register = template.Library()


@register.filter
def value(dict_, key):
    """
    dictのvalueにアクセスができる。
    {{ my_list|value:x }}
    """
    return dict_[key]


@register.filter('days_since', is_safe=False)
def days_since_filter(value):
    """
    経過日数表示に使用
    現在時刻とvalueの差分を日数で返す。1日未満は切り捨てる。
    valueがdatetime型でない、又はnative時間の場合は''を返す。
    value: datetime型
    return: str valueからの経過日数
    """
    try:
        delta = now() - value
        return f'{delta.days}日'
    except (ValueError, TypeError):
        return ''


@register.filter
def get_usernames(update_staff_form_list, i):
    """
    UpdateStaffFormのリストから指定したインデックスの
    選択可能な担当スタッフ名のリストを取得
    {{ update_staff_form_list|get_usernames:x }}

    update_staff_form_list: UpdateStaffFormのリスト
    i : UpdateStaffFormのリストのインデックス番号

    return str 選択可能なスタッフ名のリスト html形式
    """

    return update_staff_form_list[i]['staff']
