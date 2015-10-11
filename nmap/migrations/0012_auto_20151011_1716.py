# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0011_auto_20151011_1711'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nmapreportmeta',
            old_name='result',
            new_name='report',
        ),
    ]
