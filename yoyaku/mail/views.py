from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from yoyaku.booking.models import Booking
from yoyaku.mail.forms import AddressCreateUpdateForm, SendMailForm, SystemMailUpdateForm
from yoyaku.mail.models import MailAddress, MailTag, SystemMail


class SystemMailMixin:
    extra_context = {
        'segment': 'システムメール',
        'mail_tags': MailTag.objects.all().values('name', 'description'),
    }
    model = SystemMail


@method_decorator(login_required, name='dispatch')
class SystemMailListView(SystemMailMixin, ListView):
    """システムメール一覧とメールタグを表示"""
    queryset = (SystemMail.objects
                .select_related('sender')
                .values('id', 'name', 'subject', 'content', 'sender__email'))


@method_decorator(login_required, name='dispatch')
class SystemMailUpdateView(SystemMailMixin, UpdateView):
    form_class = SystemMailUpdateForm
    queryset = SystemMail.objects.select_related('sender')
    success_url = reverse_lazy('mail:システムメール一覧')

    def form_invalid(self, form):
        form.add_error(None, '入力項目に誤りがあります。確認してください。')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class EditMailView(UpdateView):
    """送信前のメール編集"""
    extra_context = {'segment': 'システムメール'}
    form_class = SendMailForm
    model = SystemMail
    queryset = SystemMail.objects.select_related('sender')
    template_name = 'mail/edit_mail.html'

    def get_object(self, queryset=None):
        """システムメールのタグを変換して返す"""
        obj = super().get_object()
        booking_id = self.kwargs.get('booking_id')
        self.booking = Booking.objects.select_related('staff', 'customer', 'booking_limit').get(id=booking_id)
        obj.replace_mail_tags(self.booking)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking'] = self.booking
        context['customer'] = self.booking.customer
        return context

    def form_valid(self, form):
        booking_id = self.kwargs.get('booking_id')
        booking = Booking.objects.select_related('customer').get(id=booking_id)
        context = {
            'object': {
                'sender': form.cleaned_data['sender'].email,
                'to': booking.customer.email,
                'subject': form.cleaned_data['subject'],
                'content': form.cleaned_data['content'],
            }
        }
        return render(self.request, 'mail/send_confirm.html', context)


@method_decorator(login_required, name='dispatch')
class SendTestMailView(DetailView):
    """テストメール送信確認画面"""
    extra_context = {
        'segment': 'システムメール',
        'is_test': True,
    }
    model = SystemMail
    queryset = SystemMail.objects.select_related('sender')
    template_name = 'mail/send_confirm.html'


@login_required()
@require_POST
def send_system_mail(request):
    """メールを送信し、結果をjson形式で返す"""
    # send_mail()は送信に成功したメッセージの数を返す。
    success = send_mail(
        request.POST['subject'],
        request.POST['content'],
        request.POST['sender'],
        [request.POST['to']],
        fail_silently=True,
    )
    params = {'msg': 'メールを送信しました。' if success else 'メールを送信できませんでした。'}
    return JsonResponse(params, json_dumps_params={'ensure_ascii': False})


class MailAddressMixin:
    extra_context = {'segment': 'メールアドレス'}
    model = MailAddress


@method_decorator(login_required, name='dispatch')
class MailAddressListView(MailAddressMixin, ListView):
    """メールアドレス一覧"""


class MailAddressFormMixin(MailAddressMixin):
    form_class = AddressCreateUpdateForm
    success_url = reverse_lazy('mail:メールアドレス一覧')

    def form_invalid(self, form):
        form.add_error(None, '入力項目に誤りがあります。確認してください。')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class MailAddressCreateView(MailAddressFormMixin, CreateView):
    """メールアドレス作成"""


@method_decorator(login_required, name='dispatch')
class MailAddressUpdateView(MailAddressFormMixin, UpdateView):
    """メールアドレス更新"""


@method_decorator(login_required, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class MailAddressDeleteView(MailAddressMixin, DeleteView):
    """メールアドレス削除"""

    model = MailAddress
    success_url = reverse_lazy('mail:メールアドレス一覧')

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')

        if SystemMail.objects.filter(sender__id=pk).exists():
            messages.info(request, '現在使用されているメールアドレスのため削除できません。')
            return HttpResponseRedirect(self.success_url)

        try:
            return super().post(request, *args, **kwargs)
        except Http404:
            # objectを取得できなかった場合
            return HttpResponseRedirect(self.success_url)
