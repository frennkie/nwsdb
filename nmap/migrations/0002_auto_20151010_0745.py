# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='updated',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 10, 7, 45, 56, 950829, tzinfo=utc), verbose_name=b'date update', auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'date created'),
        ),
    ]
