# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('email', models.CharField(max_length=200, blank=True)),
                ('comment', models.CharField(max_length=200, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'date update')),
            ],
        ),
        migrations.CreateModel(
            name='NmapReportMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_id', models.CharField(max_length=36)),
                ('task_comment', models.CharField(max_length=200)),
                ('task_created', models.DateTimeField(null=True, verbose_name=b'date task created')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'date update')),
                ('report_stored', models.BooleanField(default=False)),
                ('report', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NmapTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_id', models.CharField(max_length=36)),
                ('comment', models.CharField(max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'date update')),
                ('completed', models.BooleanField(default=False)),
                ('completed_status', models.CharField(max_length=20)),
            ],
            options={
                'permissions': (('view_task', 'Can see tasks'), ('stop_task', 'Can stop running tasks'), ('revoke_task', 'Can revoke pending tasks')),
            },
        ),
    ]
