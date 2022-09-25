import time

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

from yoyaku.accounts.models import User


class Command(BaseCommand):
    help = 'テスト用ユーザー作成'

    def add_arguments(self, parser):
        parser.add_argument('user_type', choices=['staff', 'customer'])
        parser.add_argument('-c', '--count', type=int, default=100)

    def handle(self, *args, **options):
        is_staff = True if options['user_type'] == 'staff' else False
        ut = int(time.time())
        user_list = [
            User(
                user_id=f'user{ut}{i}',
                username=f'ユーザー{ut}{i}',
                email=f'{ut}{i}@example.com',
                password=make_password('test1234'),
                is_staff=is_staff,
            ) for i in range(options['count'])
        ]
        User.objects.bulk_create(user_list)
