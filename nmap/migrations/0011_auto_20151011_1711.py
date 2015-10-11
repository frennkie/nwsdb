# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0010_auto_20151011_1617'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nmapreportmeta',
            name='report_id',
        ),
        migrations.AddField(
            model_name='nmapreportmeta',
            name='result',
            field=models.TextField(null=True),
        ),
    ]
