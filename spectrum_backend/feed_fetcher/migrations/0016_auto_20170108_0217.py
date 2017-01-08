# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-08 02:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0015_auto_20170108_0202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feeditem',
            name='author',
            field=models.CharField(default='', max_length=500),
        ),
        migrations.AlterField(
            model_name='feeditem',
            name='content',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='feeditem',
            name='description',
            field=models.CharField(default='', max_length=500),
        ),
        migrations.AlterField(
            model_name='feeditem',
            name='image_url',
            field=models.CharField(default='', max_length=500),
        ),
        migrations.AlterField(
            model_name='feeditem',
            name='raw_content',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='feeditem',
            name='raw_description',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='feeditem',
            name='summary',
            field=models.CharField(default='', max_length=500),
        ),
    ]
