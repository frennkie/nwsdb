# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0009_auto_20151011_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='nmaptask',
            name='result',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='nmapreportmeta',
            name='task_created',
            field=models.DateTimeField(null=True, verbose_name=b'date task created'),
        ),
    ]
