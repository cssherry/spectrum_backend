# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-03 18:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0005_auto_20170302_0517'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='logo_url',
            field=models.CharField(default='', max_length=500),
        ),
        migrations.AlterUniqueTogether(
            name='association',
            unique_together=set([('base_feed_item', 'associated_feed_item')]),
        ),
    ]
