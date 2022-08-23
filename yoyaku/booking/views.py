import json
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware, utc
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from yoyaku.accounts.models import User
from yoyaku.booking.forms import BookingForm, BookingLimitEditForm, BookingSearchForm, UpdateStaffForm
from yoyaku.booking.models import Booking, BookingLimit
from yoyaku.core.utils import clean_page_size
from yoyaku.booking.utils import get_time_frames, get_today0000


@method_decorator(login_required, name='dispatch')
class BookingLimitListView(TemplateView):
    """システムメール一覧とメールタグを表示"""
    extra_context = {
        'segment': '予約枠',
        'index_msg': '',
        'time_frames': get_time_frames(),
        'day_list': None,
        'rows': None,
    }
    form_class = BookingLimitEditForm
    template_name = 'booking/booking_limit_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()

        # 表示期間の生成
        self.object = None
        try:
            page_no = int(self.request.GET.get('page', 0))
            start = get_today0000() + timedelta(days=page_no * settings.DISP_DAYS)
        except (OverflowError, ValueError):
            raise Http404()

        limit_list = (
            BookingLimit.objects.prefetch_related('bookings')
            .filter(
                start_datetime__gte=str(start),
                start_datetime__lt=str(start + timedelta(days=settings.DISP_DAYS)),
            )
            .order_by('start_datetime')
        )

        context.update({
            'page_no': page_no,
            'day_list': [(start + timedelta(days=i)) for i in range(settings.DISP_DAYS)],
            'start': start,
            'limit_list': limit_list,
        })
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('booking:予約枠一覧'))
        else:
            context = self.get_context_data(form=form)
            context['form'] = form
            return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class BookingListView(ListView):
    """予約一覧"""
    extra_context = {
        'segment': '予約',
        'info': '',
    }
    query_keys = {
        'from_datetime': 'booking_limit__start_datetime__gte',
        'to_datetime': 'booking_limit__start_datetime__lt',
        'staff': 'staff_id',
        'unknown': 'staff_id',
    }
    model = Booking
    form_class = BookingSearchForm
    ordering = 'booking_limit__start_datetime'
    paginate_by = settings.PER_PAGE_SET[0]

    def get_search_str(self, data):
        """
        urlのクエリ文字列に使う検索条件の作成
        data: request.GETかrequest.POSTのデータ
        """
        result = ''
        for key in self.query_keys.keys():
            if key in data and data[key] != '':
                result += f'&{key}={data[key]}'
        return result

    def get_filter_kwargs(self, data):
        """
        クエリセットの検索条件の取得
        data: request.GETかrequest.POSTのデータ
        """
        result = {}
        if 'unknown' in data:
            result[self.query_keys['unknown']] = None

        if 'from_datetime' in data:
            # yyyy-mm-dd 形式の文字列をtimezone付きのdatetime型に変換する
            from_datetime = make_aware(datetime.strptime(data['from_datetime'], '%Y-%m-%d'))
            result[self.query_keys['from_datetime']] = from_datetime

        if 'to_datetime' in data:
            # yyyy-mm-dd 形式の文字列をtimezone付きのdatetime型に変換する
            to_datetime = make_aware(datetime.strptime(data['to_datetime'], '%Y-%m-%d'))
            result[self.query_keys['to_datetime']] = to_datetime + timedelta(days=1)

        if 'staff' in data:
            result[self.query_keys['staff']] = data['staff']

        # 検索用クエリ文字がない場合はデフォルトの検索条件をセット
        if not result:
            result = {
                'booking_limit__start_datetime__gte': get_today0000().isoformat(' '),
            }
        return result

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', settings.PER_PAGE_SET[0])
        return clean_page_size(page_size)

    def get_queryset(self, where=None):
        """
        where: dict 検索実行時の条件
        Noneならクエリパラメータから検索条件を取得
        """
        if not where:
            where = self.get_filter_kwargs(self.request.GET)
        return (
            Booking.objects.select_related('staff', 'customer', 'booking_limit')
            .filter(**where)
            .order_by(self.ordering)
        )

    def get_staff_form_list(self, page_obj):
        # 管理者以外のスタッフを表示する
        staff_choices = [('', '未定義')]
        staff_choices.extend(list(User.staffs.is_active().values_list('id', 'username')))

        result = []
        for b in page_obj.object_list:
            initial = {'staff': b.staff_id} if b.staff_id else {}

            if b.staff and not b.staff.is_active:
                deleted_staff = [(b.staff_id, b.staff.username)]
                result.append(UpdateStaffForm(choices=staff_choices + deleted_staff, initial=initial))
            else:
                result.append(UpdateStaffForm(choices=staff_choices, initial=initial))

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_form_list'] = self.get_staff_form_list(context['page_obj'])
        context['where_str'] = self.get_search_str(self.request.GET)
        context['form'] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST)

        if form.is_valid():
            self.object_list = self.get_queryset(where=form.get_where())
        else:
            self.object_list = self.get_queryset()

        context = self.get_context_data()
        context['where_str'] = self.get_search_str(self.request.POST)
        context['form'] = form
        paginator = context['paginator']
        context['info'] = form.get_info(paginator.count)

        return self.render_to_response(context)


class BookingMixin:
    extra_context = {'segment': '予約'}
    model = Booking
    form_class = BookingForm

    def form_invalid(self, form):
        form.add_error(None, '入力項目に誤りがあります。確認してください。')
        return super().form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
class BookingCreateView(BookingMixin, CreateView):
    """予約作成"""
    template_name = 'booking/create_booking.html'

    def get_initial(self):
        customer_id = self.kwargs.get('customer_id')
        self.customer = get_object_or_404(User, pk=customer_id, is_staff=False, is_active=True)
        result = {
            'customer': self.customer,
            'start_datetime': get_today0000(),
        }
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.customer
        return context

    def get_success_url(self):
        return reverse('accounts:顧客詳細', args=[self.kwargs.get('customer_id')])


@method_decorator(login_required, name='dispatch')
class BookingUpdateView(BookingMixin, UpdateView):
    """予約更新 2つのurlから利用されるViewクラス(urls.py参照)"""
    context_object_name = 'booking'
    initial = {'start_datetime': get_today0000()}
    queryset = Booking.objects.select_related('staff', 'customer', 'booking_limit').all()
    template_name = 'booking/update_booking.html'

    def get_success_url(self):
        if 'customer_detail' in self.request.path:
            return reverse('accounts:顧客詳細', args=[self.object.customer_id])
        else:
            return reverse('booking:予約一覧')


@method_decorator(login_required, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class UpdateBookingUserView(View):

    def is_ajax(self, request):
        return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    def dispatch(self, request, *args, **kwargs):
        if not self.is_ajax(request):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        result = {'msg': 'スタッフを更新しました。'}
        try:
            staff_id = request.POST['staff_id']
            booking_id = request.POST['booking_id']
            requested_at = request.POST['requested_at']
            staff = None
            if staff_id:
                staff = User.staffs.get(id=staff_id, is_active=True)
            booking = Booking.objects.get(id=booking_id)

            # 他ユーザによる更新確認
            dt = datetime.fromisoformat(requested_at).astimezone(utc)
            if booking.is_updated_by_others(dt, request.user):
                json_str = json.dumps({'msg': 'reload'}, ensure_ascii=False)
                return HttpResponse(json_str)

            booking.staff = staff
            booking.updated_by = request.user
            booking.save()
        except (Booking.DoesNotExist, User.DoesNotExist, ValueError):
            result['msg'] = 'reload'

        json_str = json.dumps(result, ensure_ascii=False)
        return HttpResponse(json_str)


@method_decorator(login_required, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class BookingDeleteView(DeleteView):
    model = Booking

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Http404:
            return HttpResponseRedirect(reverse('accounts:顧客一覧'))

    def get_success_url(self):
        return reverse('accounts:顧客詳細', args=[self.object.customer_id])
