from yoyaku.mail.models import SystemMail


def send_customer_registered_mail(booking):
    """
    予約完了メールを送信する
    booking: Bookingクラス
    """
    system_mail = SystemMail.objects.get_registered_mail()
    result = system_mail.send_system_mail(booking)
    return True if result else False
