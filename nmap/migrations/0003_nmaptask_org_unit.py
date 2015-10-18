# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0002_auto_20151015_2015'),
    ]

    operations = [
        migrations.AddField(
            model_name='nmaptask',
            name='org_unit',
            field=models.ForeignKey(default=1, to='nmap.OrgUnit'),
            preserve_default=False,
        ),
    ]
