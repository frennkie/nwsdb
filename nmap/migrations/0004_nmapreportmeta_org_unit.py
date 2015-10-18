# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nmap', '0003_nmaptask_org_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='nmapreportmeta',
            name='org_unit',
            field=models.ForeignKey(default=1, to='nmap.OrgUnit'),
            preserve_default=False,
        ),
    ]
