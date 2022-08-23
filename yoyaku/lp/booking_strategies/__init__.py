from .base import BaseBookingStrategy


def get_booking_strategy():
    """
    ホストが増える度に拡張する
    if settings.HOSTNAME == HogeStrategy.HOSTNAME:
        return Hoge()
    """
    return BaseBookingStrategy()
