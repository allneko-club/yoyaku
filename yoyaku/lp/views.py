from django.db import transaction
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from yoyaku.booking.forms import RegisterBookingForm
from yoyaku.booking.models import BookingLimit
from yoyaku.lp.booking_strategies import get_booking_strategy
from yoyaku.mail.send_mails import send_customer_registered_mail


class BookingView(TemplateView):
    """
    予約の登録には顧客情報登録用フォームと、予約登録用フォームを使う
    """
    booking_strategy = None

    def get_booking_strategy(self):
        if self.booking_strategy is None:
            self.booking_strategy = get_booking_strategy()
        return self.booking_strategy

    def get_form_kwargs(self):
        kwargs = {}
        if self.request.method == 'POST':
            kwargs.update({'data': self.request.POST})
        return kwargs

    def get_customer_form(self, post_data=None):
        return self.get_booking_strategy().get_customer_form(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'form' not in kwargs and 'form2' not in kwargs:
            context['form'] = self.get_customer_form()
            context['form2'] = RegisterBookingForm()

        if 'form2_errors' not in kwargs:
            context['form2_errors'] = []

        bl_list = BookingLimit.objects.customers_can_select(after_min=90)
        context['booking_limit_list'] = bl_list
        return context

    def get_template_names(self):
        return self.get_booking_strategy().get_booking_template_name()

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        customer_form = self.get_customer_form()
        booking_form = RegisterBookingForm(self.request.POST)
        if customer_form.is_valid() and booking_form.is_valid():
            return self.forms_valid(customer_form, booking_form)
        else:
            return self.forms_invalid(customer_form, booking_form)

    def forms_valid(self, customer_form, booking_form):
        customer = customer_form.save()
        booking = booking_form.save(customer)
        send_customer_registered_mail(booking)
        redirect_to = self.get_booking_strategy().get_booking_done_url()
        return HttpResponseRedirect(redirect_to)

    def forms_invalid(self, customer_form, booking_form):
        kwargs = {
            'form': customer_form,
            'form2': booking_form,
        }
        if not booking_form.is_valid():
            # 予約画面のカレンダー表示の都合により、予約枠エラーの場合はエラー表示用フォームと、
            # 再作成したフォームを使い分ける
            kwargs['form2_errors'] = booking_form
            kwargs['form2'] = RegisterBookingForm()
        return self.render_to_response(self.get_context_data(**kwargs))


class BookingDoneView(TemplateView):
    """予約完了ページ"""
    def get_template_names(self):
        return get_booking_strategy().get_booking_done_template_name()
