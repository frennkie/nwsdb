# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0002_auto_20151010_0745'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='comment',
            field=models.CharField(default=datetime.datetime(2015, 10, 10, 7, 53, 18, 81327, tzinfo=utc), max_length=200),
            preserve_default=False,
        ),
    ]
