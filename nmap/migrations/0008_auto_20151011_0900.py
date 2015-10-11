# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0007_nmapreportmeta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nmapreportmeta',
            name='report_id',
            field=models.IntegerField(null=True),
        ),
    ]
