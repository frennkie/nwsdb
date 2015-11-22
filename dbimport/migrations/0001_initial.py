# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('name', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('email', models.EmailField(max_length=254)),
                ('lastname', models.CharField(default='', max_length=80)),
                ('firstnames', models.CharField(default='', max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='PersonRoleCompany',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('organization', models.OneToOneField(to='dbimport.Organization')),
                ('person', models.OneToOneField(to='dbimport.Person')),
            ],
        ),
        migrations.CreateModel(
            name='Range',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('name', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='RangeDNS',
            fields=[
                ('range_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dbimport.Range')),
                ('address', models.CharField(max_length=255)),
            ],
            bases=('dbimport.range',),
        ),
        migrations.CreateModel(
            name='RangeV4',
            fields=[
                ('range_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dbimport.Range')),
                ('address', models.GenericIPAddressField(protocol='IPv4', verbose_name='IPv4 Address')),
                ('mask', models.PositiveSmallIntegerField(verbose_name='CIDR Bits', validators=[django.core.validators.MaxValueValidator(32)])),
                ('subnet_of', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='dbimport.RangeV4')),
            ],
            bases=('dbimport.range',),
        ),
        migrations.CreateModel(
            name='RangeV6',
            fields=[
                ('range_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='dbimport.Range')),
                ('address', models.GenericIPAddressField(protocol='IPv6', verbose_name='IPv6 Address')),
                ('mask', models.PositiveSmallIntegerField(verbose_name='CIDR Bits', validators=[django.core.validators.MaxValueValidator(128)])),
                ('subnet_of', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='dbimport.RangeV6')),
            ],
            bases=('dbimport.range',),
        ),
        migrations.AddField(
            model_name='range',
            name='personrolecompany',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='dbimport.PersonRoleCompany', null=True),
        ),
        migrations.AddField(
            model_name='personrolecompany',
            name='role',
            field=models.OneToOneField(to='dbimport.Role'),
        ),
    ]
