# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0004_nmaptask'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='nmaptask',
            options={'permissions': (('view_task', 'Can see tasks'), ('stop_task', 'Can stop running tasks'), ('revoke_task', 'Can revoke pending tasks'))},
        ),
    ]
