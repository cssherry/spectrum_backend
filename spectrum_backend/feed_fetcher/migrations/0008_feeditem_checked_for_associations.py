# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-19 23:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0007_auto_20170317_0807'),
    ]

    operations = [
        migrations.AddField(
            model_name='feeditem',
            name='checked_for_associations',
            field=models.BooleanField(default=0),
        ),
    ]