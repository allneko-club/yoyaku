import factory
from factory.django import DjangoModelFactory
from datetime import timedelta

from yoyaku.booking.models import Booking, BookingLimit
from yoyaku.booking.utils import get_disp_hour_from, get_today0000
from .accounts import CustomerFactory, StaffFactory


class BookingLimitFactory(DjangoModelFactory):
    class Meta:
        model = BookingLimit

    limit = 1
    start_datetime = get_today0000() + timedelta(hours=get_disp_hour_from())


class BookingFactory(DjangoModelFactory):
    class Meta:
        model = Booking

    staff = factory.SubFactory(StaffFactory)
    customer = factory.SubFactory(CustomerFactory)
    booking_limit = factory.SubFactory(BookingLimitFactory)
