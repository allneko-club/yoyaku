import urllib.parse

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from yoyaku.accounts.forms import CustomerForm, CustomerSearchForm
from yoyaku.accounts.models import User
from yoyaku.accounts.forms import StaffForm
from yoyaku.accounts.excel_export_service import get_customers_xl
from yoyaku.core.utils import clean_page_size


@method_decorator(login_required, name='dispatch')
class StaffListView(ListView):
    """
    管理者以外のスタッフを表示する。
    表示件数の切り替えができる。
    """
    extra_context = {'segment': 'スタッフ'}
    model = User
    queryset = User.staffs.is_active().values('id', 'user_id', 'username')
    ordering = '-id'
    template_name = 'accounts/staff_list.html'

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', settings.PER_PAGE_SET[0])
        return clean_page_size(page_size)


class StaffFormMixin:
    form_class = StaffForm
    model = User
    success_url = reverse_lazy('accounts:スタッフ一覧')
    template_name = 'accounts/staff_form.html'

    def form_invalid(self, form):
        form.add_error(None, '入力項目に誤りがあります。確認してください。')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class StaffCreateView(StaffFormMixin, CreateView):
    extra_context = {'segment': 'スタッフ', 'title': 'スタッフ登録'}


@method_decorator(login_required, name='dispatch')
class StaffUpdateView(StaffFormMixin, UpdateView):
    extra_context = {'segment': 'スタッフ', 'title': 'スタッフ編集'}
    queryset = User.staffs.is_active()

    def form_valid(self, form):
        # 自分自身を編集した場合、自動で再ログインする
        self.object = form.save()
        if self.object.id == self.request.user.id:
            update_self = authenticate(
                user_id=self.object.user_id,
                password=self.request.POST['password1'],
            )
            login(self.request, update_self)
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class StaffDeleteView(DeleteView):
    model = User
    queryset = User.staffs.is_active()
    success_url = reverse_lazy('accounts:スタッフ一覧')

    def post(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            obj.is_active = False
            obj.save()
            return HttpResponseRedirect(self.success_url)
        except Http404:
            return HttpResponseRedirect(self.success_url)


@method_decorator(login_required, name='dispatch')
class CustomerListView(ListView):
    """
    検索条件にマッチした管理者以外のスタッフを表示する。
    最初は管理者以外のスタッフを全件表示する。
    pが不正な値の場合はPage.get_page()の機能により最初か最後のページが表示される
    """
    extra_context = {
        'segment': '顧客',
    }
    filter_keys = {
        'username': '__icontains',
        'furigana': '__icontains',
        'email': '__icontains',
        'phone_number': '__icontains',
    }
    model = User
    form_class = CustomerSearchForm
    ordering = '-id'
    queryset = User.customers.is_active().select_related('booking__booking_limit', 'booking__staff')
    paginate_by = settings.PER_PAGE_SET[0]
    template_name = 'accounts/customer_list.html'

    def get_search_str(self, data):
        """
        urlのクエリ文字列に使う検索条件の作成
        data: request.GETかrequest.POSTのデータ
        """
        result = ''
        for key in self.filter_keys.keys():
            if key in data and data[key]:
                result += f'&{key}={data[key]}'
        return result

    def get_filter_kwargs(self, data):
        """
        クエリセットの検索条件の取得
        data: request.GETかrequest.POSTのデータ
        data[k] 空でない場合
        """
        result = {}
        for k, v in self.filter_keys.items():
            if k in data and data[k]:
                result[k + v] = data[k]
        return result

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', settings.PER_PAGE_SET[0])
        return clean_page_size(page_size)

    def get_queryset(self, where=None):
        if not where:
            where = self.get_filter_kwargs(self.request.GET)
        return self.queryset.filter(**where).order_by(self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['where_str'] = self.get_search_str(self.request.GET)
        if self.request.method == 'POST':
            context['where_str'] = self.get_search_str(self.request.POST)

        context['form'] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            where = self.get_filter_kwargs(self.request.POST)
            self.object_list = self.get_queryset(where=where)
        else:
            self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required, name='dispatch')
class CustomerDetailView(DetailView):
    extra_context = {'segment': '顧客'}
    model = User
    queryset = User.customers.is_active().select_related('booking__staff')
    template_name = 'accounts/customer_detail.html'


class CustomerMixin:
    model = User
    form_class = CustomerForm
    template_name = 'accounts/customer_form.html'

    def form_invalid(self, form):
        form.add_error(None, '入力項目に誤りがあります。確認してください。')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class CustomerCreateView(CustomerMixin, CreateView):
    extra_context = {'segment': '顧客', 'title': '顧客登録'}
    success_url = reverse_lazy('accounts:顧客一覧')


@method_decorator(login_required, name='dispatch')
class CustomerUpdateView(CustomerMixin, UpdateView):
    extra_context = {'segment': '顧客', 'title': '顧客編集'}

    def get_success_url(self):
        return reverse('accounts:顧客詳細', args=[self.object.id])


@method_decorator(login_required, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class CustomerDeleteView(DeleteView):
    model = User
    queryset = User.customers.is_active()

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                customer = self.get_object()
                customer.is_active = False
                customer.save()
                customer.booking.delete()
                return HttpResponseRedirect(reverse('accounts:顧客一覧'))
        except Http404:
            return HttpResponseRedirect(reverse('accounts:顧客一覧'))


@login_required()
@require_POST
def customer_list_download(request):
    """
    エクセルファイルに顧客の全データを書き出しダウンロードする
    quote()でファイル名に日本語を使えるようにしている。
    """
    if not request.user.is_superuser:
        raise PermissionDenied()

    filename = '顧客一括データ.xls'
    quoted_filename = urllib.parse.quote(filename)
    xl = get_customers_xl()
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f"attachment; filename='{quoted_filename}'; filename*=UTF-8''{quoted_filename}"
    xl.save(response)
    return response
