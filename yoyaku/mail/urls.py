from django.urls import path

from yoyaku.mail import views

app_name = 'mail'
urlpatterns = [
    path('system_mail/', views.SystemMailListView.as_view(), name='システムメール一覧'),
    path('system_mail/<int:pk>/edit', views.SystemMailUpdateView.as_view(), name='システムメール編集'),

    path('address/', views.MailAddressListView.as_view(), name='メールアドレス一覧'),
    path('address/create', views.MailAddressCreateView.as_view(), name='メールアドレス登録'),
    path('address/<int:pk>/update', views.MailAddressUpdateView.as_view(), name='メールアドレス編集'),
    path('address/<int:pk>/delete', views.MailAddressDeleteView.as_view(), name='メールアドレス削除'),

    path('edit/<int:pk>/<int:booking_id>', views.EditMailView.as_view(), name='メール編集'),
    path('send_testmail/<int:pk>', views.SendTestMailView.as_view(), name='テストメール送信'),
    path('send_mail', views.send_system_mail, name='メール送信'),
]
