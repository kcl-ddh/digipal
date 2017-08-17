# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0002_auto_20170705_0056'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='date_sort',
            field=models.CharField(
                help_text=b'Optional date used for sorting HI or visualising HI on timeline. It is interpretable and bounded: e.g. 1200 x 1229.', max_length=128, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='historicalitem',
            name='date',
            field=models.CharField(
                help_text=b'Date of the Historical Item', max_length=128, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='historicalitem',
            name='date_sort',
            field=models.CharField(
                help_text=b'Optional date used for sorting HI or visualising HI on timeline. It is interpretable and bounded: e.g. 1200 x 1229.', max_length=128, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='date',
            field=models.CharField(
                help_text=b'Date of the Historical Item', max_length=128, null=True, blank=True),
        ),
    ]
