from django.urls import reverse

from yoyaku.accounts.forms import RegisterCustomerForm


class BaseBookingStrategy:
    HOSTNAME = ''

    def get_customer_form(self, **kwargs):
        return RegisterCustomerForm(**kwargs)

    def get_booking_template_name(self):
        return 'lp/booking_form.html'

    def get_booking_done_url(self):
        return reverse('lp:予約完了')

    def get_booking_done_template_name(self):
        return 'lp/booking_done.html'
