# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0008_textitempart_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='repository',
            options={'ordering': ['place', 'short_name', 'name'], 'verbose_name_plural': 'Repositories'},
        ),
        migrations.AddField(
            model_name='allograph',
            name='illustration',
            field=models.ImageField(null=True, upload_to=b'uploads/images/', blank=True),
        ),
    ]
