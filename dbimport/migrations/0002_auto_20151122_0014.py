# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbimport', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PersonRoleCompany',
            new_name='PersonRoleOrganization',
        ),
        migrations.RenameField(
            model_name='range',
            old_name='personrolecompany',
            new_name='personroleorganization',
        ),
    ]
