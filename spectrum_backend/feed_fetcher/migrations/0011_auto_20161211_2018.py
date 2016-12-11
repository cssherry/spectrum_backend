# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-11 20:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed_fetcher', '0010_auto_20161211_0228'),
    ]

    operations = [
        migrations.AddField(
            model_name='feeditem',
            name='topics',
            field=models.ManyToManyField(to='feed_fetcher.Topic'),
        ),
        migrations.AlterField(
            model_name='topicword',
            name='pos_type',
            field=models.CharField(choices=[('CD', 'numeral, cardinal'), ('FW', 'foreign word'), ('LOC', 'proper noun, location'), ('NAME', "proper noun, person's name"), ('NOUN', 'common noun'), ('ORG', "proper noun, organization's name"), ('VERB', 'verb'), ('XX', 'uncategorized')], max_length=5),
        ),
    ]
