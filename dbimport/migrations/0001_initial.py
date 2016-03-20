# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipPRORange',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('name', models.CharField(max_length=80)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('email', models.EmailField(max_length=254)),
                ('last_name', models.CharField(default='', max_length=80)),
                ('first_names', models.CharField(default='', max_length=80, blank=True)),
                ('salutation', models.CharField(max_length=5, choices=[('MR', 'Mr.'), ('MRS', 'Mrs.'), ('MS', 'Ms.'), ('OTHER', 'Other')])),
            ],
            options={
                'ordering': ['email'],
            },
        ),
        migrations.CreateModel(
            name='RangeDNS',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('duplicates_allowed', models.BooleanField(default=False)),
                ('is_duplicate', models.BooleanField(default=False, editable=False)),
                ('address', models.CharField(max_length=255)),
                ('membershipprorange', models.ForeignKey(verbose_name='Relation', to='dbimport.MembershipPRORange')),
            ],
            options={
                'ordering': ['address'],
            },
        ),
        migrations.CreateModel(
            name='RangeV4',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('address_binary', models.BinaryField(verbose_name='IP as Binary', max_length=16)),
                ('duplicates_allowed', models.BooleanField(default=False)),
                ('is_duplicate', models.BooleanField(default=False, editable=False)),
                ('address', models.GenericIPAddressField(protocol='IPv4', verbose_name='Network Address (IPv4)')),
                ('mask', models.PositiveSmallIntegerField(verbose_name='Mask in Bits (e.g. /24)', validators=[django.core.validators.MaxValueValidator(32)])),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('membershipprorange', models.ForeignKey(verbose_name='Relation', to='dbimport.MembershipPRORange')),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='dbimport.RangeV4', null=True)),
            ],
            options={
                'ordering': ['address_binary', 'mask'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RangeV6',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('address_binary', models.BinaryField(verbose_name='IP as Binary', max_length=16)),
                ('duplicates_allowed', models.BooleanField(default=False)),
                ('is_duplicate', models.BooleanField(default=False, editable=False)),
                ('address', models.GenericIPAddressField(protocol='IPv6', verbose_name='IPv6 Address')),
                ('mask', models.PositiveSmallIntegerField(verbose_name='CIDR Bits', validators=[django.core.validators.MaxValueValidator(128)])),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('membershipprorange', models.ForeignKey(verbose_name='Relation', to='dbimport.MembershipPRORange')),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='dbimport.RangeV6', null=True)),
            ],
            options={
                'ordering': ['address_binary', 'mask'],
                'abstract': False,
            },
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
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='membershipprorange',
            name='organization',
            field=models.ForeignKey(to='dbimport.Organization'),
        ),
        migrations.AddField(
            model_name='membershipprorange',
            name='person',
            field=models.ForeignKey(to='dbimport.Person'),
        ),
        migrations.AddField(
            model_name='membershipprorange',
            name='role',
            field=models.ForeignKey(to='dbimport.Role'),
        ),
        migrations.AlterUniqueTogether(
            name='membershipprorange',
            unique_together=set([('person', 'organization')]),
        ),
    ]
