# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='range',
            name='membership',
            field=models.ForeignKey(default='6095f909c9a64c16bcdee6a194c25136', to='dbimport.Membership'),
            preserve_default=False,
        ),
    ]
