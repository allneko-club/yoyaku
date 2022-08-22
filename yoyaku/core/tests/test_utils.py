from django.conf import settings
from django.test import TestCase, override_settings

from yoyaku.core.utils import clean_page_size


class TestUtils(TestCase):

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_clean_page_size(self):
        """正常系のテスト"""
        for i in ('1', 1):
            with self.subTest(i=i):
                result = clean_page_size(i)
                self.assertEqual(result, 1)

        result = clean_page_size(3)
        self.assertEqual(result, 3)

    @override_settings(PER_PAGE_SET=[1, 2, 3])
    def test_clean_page_size_invalid_values(self):
        """異常系のテスト"""
        for i in (0, 4, 'a'):
            with self.subTest(i=i):
                result = clean_page_size(i)
                self.assertEqual(result, settings.PER_PAGE_SET[0])
