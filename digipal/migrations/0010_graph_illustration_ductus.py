# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0009_auto_20201002_2358'),
    ]

    operations = [
        migrations.AddField(
            model_name='graph',
            name='illustration_ductus',
            field=models.ImageField(null=True, upload_to=b'uploads/images/', blank=True),
        ),
    ]
