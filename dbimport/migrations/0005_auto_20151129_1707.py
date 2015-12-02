# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0004_auto_20151128_2348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rangev4',
            name='address',
            field=models.GenericIPAddressField(verbose_name='Network Address (IPv4)', editable=False, protocol='IPv4'),
        ),
        migrations.AlterField(
            model_name='rangev4',
            name='address_integer',
            field=models.BigIntegerField(verbose_name='IPv4 as Integer', editable=False, db_index=True),
        ),
        migrations.AlterField(
            model_name='rangev4',
            name='mask',
            field=models.PositiveSmallIntegerField(verbose_name='Mask in Bits (e.g. /24)', editable=False, validators=[django.core.validators.MaxValueValidator(32)]),
        ),
    ]
