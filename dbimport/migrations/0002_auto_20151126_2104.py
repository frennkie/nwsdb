# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rangev4',
            name='rangev4_relationships',
            field=models.ManyToManyField(related_name='_rangev4_relationships_+', through='dbimport.V4ParentChildRelation', to='dbimport.RangeV4'),
        ),
    ]
