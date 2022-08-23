from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

admin_prefix = settings.YOYAKU_ADMIN_PATH

app_name = 'yoyaku'
urlpatterns = [
    path('admin/', admin.site.urls),

    path(f'{admin_prefix}/', include('yoyaku.authentication.urls')),
    path(f'{admin_prefix}/account/', include('yoyaku.accounts.urls')),
    path(f'{admin_prefix}/booking/', include('yoyaku.booking.urls')),
    path(f'{admin_prefix}/mail/', include('yoyaku.mail.urls')),

    path('lp/', include('yoyaku.lp.urls')),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
