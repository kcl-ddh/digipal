# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0007_auto_20190407_2139'),
    ]

    operations = [
        migrations.AddField(
            model_name='textitempart',
            name='name',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
