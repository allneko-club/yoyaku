# Generated by Django 4.1 on 2022-09-25 02:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='row_password',
        ),
    ]
