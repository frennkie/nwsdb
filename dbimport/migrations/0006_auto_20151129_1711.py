# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0005_auto_20151129_1707'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rangev4',
            name='address',
            field=models.GenericIPAddressField(protocol='IPv4', verbose_name='Network Address (IPv4)'),
        ),
        migrations.AlterField(
            model_name='rangev4',
            name='mask',
            field=models.PositiveSmallIntegerField(verbose_name='Mask in Bits (e.g. /24)', validators=[django.core.validators.MaxValueValidator(32)]),
        ),
    ]
