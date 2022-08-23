from django.conf import settings


def clean_page_size(size):
    """
    表示数をPER_PAGE_SETに登録されている表示数に直す
    size: str or int 一覧ページの表示数
    """
    try:
        return int(size) if int(size) in settings.PER_PAGE_SET else settings.PER_PAGE_SET[0]
    except ValueError:
        return settings.PER_PAGE_SET[0]
