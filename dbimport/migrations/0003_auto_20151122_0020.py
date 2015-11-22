# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0002_auto_20151122_0014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personroleorganization',
            name='organization',
            field=models.ForeignKey(to='dbimport.Organization'),
        ),
        migrations.AlterField(
            model_name='personroleorganization',
            name='person',
            field=models.ForeignKey(to='dbimport.Person'),
        ),
        migrations.AlterField(
            model_name='personroleorganization',
            name='role',
            field=models.ForeignKey(to='dbimport.Role'),
        ),
    ]
