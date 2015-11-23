# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0003_auto_20151123_2205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rangev4',
            name='subnet_of',
            field=models.ManyToManyField(related_name='_subnet_of_+', to='dbimport.RangeV4', blank=True),
        ),
    ]
