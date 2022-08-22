import factory
from django.contrib.auth.hashers import make_password
from factory.django import DjangoModelFactory

from yoyaku.accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    user_id = factory.Sequence(lambda n: 'user_id%d' % n)
    username = factory.Sequence(lambda n: 'ユーザー%d' % n)
    email = factory.Sequence(lambda n: 'test%d@example.com' % n)

    password = make_password('password')


class StaffFactory(UserFactory):
    username = factory.Sequence(lambda n: 'スタッフ%d' % n)
    is_staff = True


class SuperUserFactory(StaffFactory):
    user_id = 'admin'
    username = 'admin'
    is_superuser = True


def get_username(n):
    choices = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ']
    result = 'ユーザー'
    str_num = str(n)
    for s in str_num:
        result += choices[int(s)]
    return result


class CustomerFactory(UserFactory):
    phone_number = factory.Sequence(lambda n: '%011d' % n)
    username = factory.Sequence(get_username)

