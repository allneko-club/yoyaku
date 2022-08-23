import re
import unicodedata

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

user_id_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_-]+$', message='ユーザIDは半角英数字と-_が使用できます。', code='invalid_character'
)

# 電話番号
phone_number_validator = RegexValidator(
    regex=r'^[0-9]{10,11}$', message='電話番号は半角数字でハイフンなしで入力してください。', code='phone_number_pattern'
)

# 郵便番号
zip_code_validator = RegexValidator(
    regex=r'^[0-9]{7}$', message='郵便番号はハイフンなしの半角数字で入力してください。', code='zip_code_pattern'
)

# 全角カタカナ
# https://ja.wikipedia.org/wiki/%E7%89%87%E4%BB%AE%E5%90%8D_(Unicode%E3%81%AE%E3%83%96%E3%83%AD%E3%83%83%E3%82%AF)
furigana_validator = RegexValidator(
    regex='^[\u30A1-\u30FF]+$', message='フリガナは全角カタカナで入力してください。', code='katakana_pattern'
)


def fullwidth_and_fa_validator(char, field_name=''):
    """英数字、特殊文字を除く全角文字"""
    if unicodedata.east_asian_width(char) in ('F', 'A'):
        raise ValidationError('%sに英数字や特殊文字は使用できません。' % field_name, code='invalid')
    elif unicodedata.east_asian_width(char) in ('H', 'Na', 'N'):
        raise ValidationError('%sは全角文字で入力してください。' % field_name, code='invalid')


def fullwidth_validator(char, field_name=''):
    if unicodedata.east_asian_width(char) in ('H', 'Na', 'N'):
        raise ValidationError('%sは全角文字で入力してください。' % field_name, code='invalid')


def validate_username(value):
    """顧客名用バリデーション"""
    value = re.sub(r'\s+', '', value)
    for char in value:
        fullwidth_and_fa_validator(char, 'お名前')


def validate_job(value):
    """職業用バリデーション"""
    value = re.sub(r'\s+', '', value)
    for char in value:
        fullwidth_validator(char, '職業')
