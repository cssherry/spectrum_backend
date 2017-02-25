# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-25 21:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0019_auto_20170112_2311'),
    ]

    operations = [
        migrations.AddField(
            model_name='feeditem',
            name='content_missing',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='publication',
            name='skip_scraping',
            field=models.BooleanField(default=0),
        ),
    ]
