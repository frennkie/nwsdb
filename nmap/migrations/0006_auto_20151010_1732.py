# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0005_auto_20151010_1728'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nmaptask',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]
