import factory
from factory.django import DjangoModelFactory

from yoyaku.mail.models import MailAddress, SystemMail


class MailAddressFactory(DjangoModelFactory):
    class Meta:
        model = MailAddress

    email = factory.Sequence(lambda n: 'test%d@example.com' % n)


class SystemMailFactory(DjangoModelFactory):
    class Meta:
        model = SystemMail

    name = factory.Sequence(lambda n: 'system_mail%d' % n)