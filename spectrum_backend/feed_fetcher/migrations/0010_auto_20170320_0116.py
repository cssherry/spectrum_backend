# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-20 01:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0009_auto_20170320_0057'),
    ]

    operations = [
        migrations.RenameField(
            model_name='feeditem',
            old_name='original_url',
            new_name='redirected_url',
        ),
    ]