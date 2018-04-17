# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-13 21:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsmessage',
            name='body',
            field=models.TextField(db_index=True),
        ),
        migrations.AlterField(
            model_name='smsmessage',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='smsmessage',
            name='from_number',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='smsmessage',
            name='sid',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='smsmessage',
            name='to_number',
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]