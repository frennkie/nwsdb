# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rangev4',
            options={'ordering': ['address', 'mask']},
        ),
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
        migrations.AlterField(
            model_name='rangev4',
            name='subnet_of',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='dbimport.RangeV4', null=True),
        ),
    ]
