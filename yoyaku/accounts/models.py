from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import UserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from yoyaku.core.exceptions.field_validatiors import *


class Sex(models.Model):
    """性別のマスターモデル"""
    name = models.CharField(_('性別'), max_length=16, unique=True)
    rank = models.PositiveIntegerField(_('表示順'), unique=True)


class Ages(models.Model):
    """年代のマスターモデル"""
    name = models.CharField(_('年代'), max_length=16, unique=True)
    rank = models.PositiveIntegerField(_('表示順'), unique=True)

    def __str__(self):
        return self.name


class StaffManager(models.Manager):
    """スーパーユーザーを除くスタッフ権限のユーザーを取得"""
    def get_queryset(self):
        return super().get_queryset().filter(is_superuser=False, is_staff=True)

    def is_active(self):
        return self.filter(is_active=True)

    def create(self, **kwargs):
        kwargs['is_staff'] = True
        return super(StaffManager, self).create(**kwargs)


class CustomerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_superuser=False, is_staff=False)

    def is_active(self):
        return self.filter(is_active=True)


class User(AbstractBaseUser, PermissionsMixin):
    USERID_MAX_LENGTH = 32
    USERNAME_MAX_LENGTH = 32
    PASSWORD_MAX_LENGTH = 128

    user_id = models.CharField(
        _('ユーザID'),
        max_length=USERID_MAX_LENGTH,
        help_text=_('（半角英数と-_が使用可能。 最大%s文字）' % USERID_MAX_LENGTH),
        validators=[user_id_validator],
        unique=True,
        error_messages={'unique': '入力されたユーザIDは利用できません。'},
    )
    username = models.CharField(
        _('名前'),
        max_length=USERNAME_MAX_LENGTH,
        help_text=_('（最大%s文字）' % USERNAME_MAX_LENGTH),
    )
    email = models.EmailField(
        _('メールアドレス'),
        unique=True,
        null=True,
        error_messages={'unique': '入力されたメールアドレスは既に登録済みです。'},
    )
    is_staff = models.BooleanField(_('スタッフの状態'), default=False)
    is_active = models.BooleanField(_('有効フラグ'), default=True)
    date_joined = models.DateTimeField(_('作成日時'), default=timezone.now)

    furigana = models.CharField(
        _('フリガナ'),
        max_length=32,
        validators=[furigana_validator],
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        _('電話番号'),
        max_length=11,
        validators=[phone_number_validator],
        unique=True,
        null=True,
        error_messages={'unique': '入力された電話番号は既に登録済みです。'},
    )
    linename = models.CharField(_('LINE名'), max_length=32, null=True, blank=True)
    age = models.PositiveIntegerField(_('年齢'), null=True, blank=True)
    ages = models.ForeignKey(Ages, on_delete=models.SET_NULL, null=True, blank=True)
    job = models.CharField(_('職業'), max_length=32, validators=[validate_job], null=True, blank=True)
    zip_code = models.CharField(_('郵便番号'), max_length=7, validators=[zip_code_validator], null=True, blank=True)
    zip = models.CharField(_('住所'), max_length=200, null=True, blank=True)
    workable_time = models.CharField(_('作業可能時間'), max_length=250, null=True, blank=True)
    side_business_experience = models.CharField(_('副業経験'), max_length=16, null=True, blank=True)
    contact = models.CharField(_('お問い合わせ内容'), max_length=1000, null=True, blank=True)
    memo1 = models.CharField(_('メモ1'), max_length=500, null=True, blank=True)
    memo2 = models.CharField(_('メモ2'), max_length=2000, null=True, blank=True)

    objects = UserManager()
    staffs = StaffManager()
    customers = CustomerManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['username', 'email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def __str__(self):
        return self.username
