# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-08 08:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0002_auto_20180703_2059'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='files',
            name='category',
        ),
        migrations.AddField(
            model_name='movie_infos',
            name='category',
            field=models.ManyToManyField(to='frontend.Category'),
        ),
    ]
