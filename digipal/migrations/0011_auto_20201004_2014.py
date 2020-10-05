# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0010_graph_illustration_ductus'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='graph',
            name='illustration_ductus',
        ),
        migrations.AddField(
            model_name='annotation',
            name='illustration_ductus',
            field=models.ImageField(null=True, upload_to=b'uploads/images/', blank=True),
        ),
    ]
