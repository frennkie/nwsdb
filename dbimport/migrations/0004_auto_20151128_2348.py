# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0003_rangev4_address_integer'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rangev4',
            options={'ordering': ['address_integer', 'mask']},
        ),
    ]
