# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-22 20:20
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='rangev4',
            managers=[
                ('_default_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='rangev6',
            managers=[
                ('_default_manager', django.db.models.manager.Manager()),
            ],
        ),
    ]