# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-25 22:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0021_remove_feeditem_content_missing'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topicword',
            name='topic',
        ),
        migrations.RemoveField(
            model_name='association',
            name='topics',
        ),
        migrations.RemoveField(
            model_name='feeditem',
            name='topics',
        ),
        migrations.DeleteModel(
            name='Topic',
        ),
        migrations.DeleteModel(
            name='TopicWord',
        ),
    ]