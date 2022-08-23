from django.urls import path

from yoyaku.accounts import views

app_name = 'accounts'
urlpatterns = [
    path('staff/', views.StaffListView.as_view(), name='スタッフ一覧'),
    path('staff/create', views.StaffCreateView.as_view(), name='スタッフ登録'),
    path('staff/<int:pk>/edit', views.StaffUpdateView.as_view(), name='スタッフ編集'),
    path('staff/<int:pk>/delete', views.StaffDeleteView.as_view(), name='スタッフ削除'),

    path('customer/', views.CustomerListView.as_view(), name='顧客一覧'),
    path('customer/<int:pk>/detail', views.CustomerDetailView.as_view(), name='顧客詳細'),
    path('customer/create', views.CustomerCreateView.as_view(), name='顧客登録'),
    path('customer/<int:pk>/update', views.CustomerUpdateView.as_view(), name='顧客編集'),
    path('customer/<int:pk>/delete', views.CustomerDeleteView.as_view(), name='顧客削除'),
    path('customer_list_download', views.customer_list_download, name='顧客一覧ダウンロード'),
]
