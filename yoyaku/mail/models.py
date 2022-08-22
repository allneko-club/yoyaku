from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class MailAddress(models.Model):
    email = models.EmailField(
        _('メールアドレス'),
        unique=True,
        error_messages={'unique': '入力されたメールアドレスは既に登録済みです。'},
    )
    memo = models.TextField(_('メモ'), max_length=200, blank=True)
    created_at = models.DateTimeField(_('作成日時'), default=timezone.now)

    def __str__(self):
        return self.email


class MailTag(models.Model):
    name = models.CharField(_('名前'), max_length=64, unique=True)
    description = models.CharField(_('説明'), max_length=512)

    def __str__(self):
        return self.name


class SystemMailManager(models.Manager):
    """スーパーユーザーを除くスタッフ権限のユーザーを取得"""

    def get_registered_mail(self):
        return self.get(id=1)


class SystemMail(models.Model):
    name = models.CharField(_('名前'), max_length=64, unique=True)
    sender = models.ForeignKey(MailAddress, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(_('件名'), max_length=64, blank=True)
    content = models.CharField(_('本文'), max_length=2000, blank=True)
    created_at = models.DateTimeField(_('作成日時'), default=timezone.now)

    objects = SystemMailManager()

    def __str__(self):
        return self.name

    def replace_mail_tags(self, booking):
        """
        subjectとcontentのMailTagを置換する. 置換先がNoneの場合は置換しない。
        booking: Bookingクラス
        """
        tag_replace_map = {
            '__NAME__': booking.customer.username,
            '__MAILADDRESS__': booking.customer.email,
            '__TEL__': booking.customer.phone_number,
            '__RESERVATION_DATE__': booking.booking_limit.formatted_start_datetime(),
        }
        for tag, new in tag_replace_map.items():
            if new is None:
                continue
            self.subject = self.subject.replace(tag, new)
            self.content = self.content.replace(tag, new)

    def send_system_mail(self, booking):
        """
        send_mail()は送信に成功したメッセージの数を返す。
        booking: Bookingクラス
        """
        self.replace_mail_tags(booking)
        return send_mail(
            self.subject,
            self.content,
            self.sender.email,
            [booking.customer.email],
            fail_silently=True
        )
