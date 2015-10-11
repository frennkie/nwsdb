# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0008_auto_20151011_0900'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nmapreportmeta',
            old_name='task_task_id',
            new_name='task_id',
        ),
    ]
