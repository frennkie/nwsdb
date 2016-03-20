# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0002_auto_20151128_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='rangev4',
            name='address_integer',
            field=models.BigIntegerField(default=0, verbose_name='IPv4 as Integer', editable=False),
            preserve_default=False,
        ),
    ]
