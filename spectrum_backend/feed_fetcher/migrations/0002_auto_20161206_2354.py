# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-06 23:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feeditem',
            name='publication_date',
            field=models.DateTimeField(),
        ),
    ]
