from django.urls import path

from yoyaku.authentication import views

app_name = 'authentication'
urlpatterns = [
    path('', views.UserLoginView.as_view(), name='login'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
]
