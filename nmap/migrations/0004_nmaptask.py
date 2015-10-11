# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0003_contact_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='NmapTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_id', models.CharField(max_length=36)),
                ('comment', models.CharField(max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'date update')),
                ('completed', models.BooleanField()),
                ('completed_status', models.CharField(max_length=20)),
            ],
        ),
    ]
