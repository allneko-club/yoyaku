from django.urls import path

from yoyaku.booking import views

app_name = 'booking'
urlpatterns = [
    path('limit', views.BookingLimitListView.as_view(), name='予約枠一覧'),

    path('', views.BookingListView.as_view(), name='予約一覧'),
    path('create/<int:customer_id>', views.BookingCreateView.as_view(), name='予約登録'),
    path('<int:pk>/update/customer_detail', views.BookingUpdateView.as_view(), name='予約変更_顧客詳細'),
    path('<int:pk>/update', views.BookingUpdateView.as_view(), name='予約変更'),
    path('<int:pk>/delete', views.BookingDeleteView.as_view(), name='予約削除'),
    path('update_booking_user', views.UpdateBookingUserView.as_view(), name='予約担当変更'),
]
