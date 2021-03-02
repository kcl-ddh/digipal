# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0005_contentattribution'),
        ('digipal_text', '0002_auto_20170705_0056'),
    ]

    operations = [
        migrations.AddField(
            model_name='textcontent',
            name='attribution',
            field=models.ForeignKey(blank=True, to='digipal.ContentAttribution', null=True),
        ),
    ]
