from django.urls import path

from yoyaku.lp import views

app_name = 'lp'
urlpatterns = [
    path('booking_form', views.BookingView.as_view(), name='予約フォーム'),
    path('booking_done', views.BookingDoneView.as_view(), name='予約完了'),
]
