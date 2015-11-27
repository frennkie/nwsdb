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
                ('duplicates_allowed', models.BooleanField(default=False)),
                ('is_duplicate', models.BooleanField(default=False, editable=False)),
                ('address', models.GenericIPAddressField(protocol='IPv4', verbose_name='Network Address (IPv4)')),
                ('mask', models.PositiveSmallIntegerField(verbose_name='Mask in Bits (e.g. /24)', validators=[django.core.validators.MaxValueValidator(32)])),
                ('membershipprorange', models.ForeignKey(verbose_name='Relation', to='dbimport.MembershipPRORange')),
                ('parent_range', models.OneToOneField(related_name='+', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='dbimport.RangeV4')),
            ],
            options={
                'ordering': ['address', 'mask'],
            },
        ),
        migrations.CreateModel(
            name='RangeV6',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('comment', models.CharField(default='', max_length=255, blank=True)),
                ('duplicates_allowed', models.BooleanField(default=False)),
                ('is_duplicate', models.BooleanField(default=False, editable=False)),
                ('address', models.GenericIPAddressField(protocol='IPv6', verbose_name='IPv6 Address')),
                ('mask', models.PositiveSmallIntegerField(verbose_name='CIDR Bits', validators=[django.core.validators.MaxValueValidator(128)])),
                ('membershipprorange', models.ForeignKey(verbose_name='Relation', to='dbimport.MembershipPRORange')),
                ('subnet_of', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='dbimport.RangeV6')),
            ],
            options={
                'ordering': ['address'],
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
        migrations.CreateModel(
            name='V4ParentChildRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='date update')),
                ('status', models.IntegerField(choices=[(1, 'Parent'), (2, 'Child')])),
                ('from_rangev4', models.ForeignKey(related_name='from_rangev4', to='dbimport.RangeV4')),
                ('to_rangev4', models.ForeignKey(related_name='to_rangev4', to='dbimport.RangeV4')),
            ],
        ),
        migrations.AddField(
            model_name='rangev4',
            name='rangev4_relationships',
            field=models.ManyToManyField(related_name='related_to', through='dbimport.V4ParentChildRelation', to='dbimport.RangeV4'),
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
