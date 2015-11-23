# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0002_auto_20151123_2153'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rangev4',
            name='subnet_of',
        ),
        migrations.AddField(
            model_name='rangev4',
            name='subnet_of',
            field=models.ManyToManyField(related_name='_subnet_of_+', null=True, to='dbimport.RangeV4', blank=True),
        ),
    ]
