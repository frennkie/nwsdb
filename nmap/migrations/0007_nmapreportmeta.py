# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0006_auto_20151010_1732'),
    ]

    operations = [
        migrations.CreateModel(
            name='NmapReportMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_task_id', models.CharField(max_length=36)),
                ('task_comment', models.CharField(max_length=200)),
                ('task_created', models.DateTimeField(auto_now_add=True, verbose_name=b'date task created')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'date update')),
                ('report_stored', models.BooleanField(default=False)),
                ('report_id', models.IntegerField()),
            ],
        ),
    ]
