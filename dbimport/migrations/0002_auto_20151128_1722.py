# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='v4parentchildrelation',
            name='from_rangev4',
        ),
        migrations.RemoveField(
            model_name='v4parentchildrelation',
            name='to_rangev4',
        ),
        migrations.DeleteModel(
            name='V4ParentChildRelation',
        ),
    ]
