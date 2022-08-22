from django.conf import settings as ss


def settings(request):
    return {
        'PER_PAGE_SET': ss.PER_PAGE_SET,
        'START_TIME': ss.START_TIME,
        'END_TIME': ss.END_TIME,
        'SITE_NAME': ss.SITE_NAME,
    }
