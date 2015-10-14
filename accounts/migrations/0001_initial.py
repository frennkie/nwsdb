# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='OrgUnit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('comment', models.CharField(max_length=200, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'date update')),
                ('members', models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='accounts.Membership')),
            ],
        ),
        migrations.AddField(
            model_name='membership',
            name='org',
            field=models.ForeignKey(to='accounts.OrgUnit'),
        ),
        migrations.AddField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
