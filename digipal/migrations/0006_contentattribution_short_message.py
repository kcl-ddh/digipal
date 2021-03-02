# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0005_contentattribution'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentattribution',
            name='short_message',
            field=tinymce.models.HTMLField(help_text=b"Shown under the text in the Text Viewer. Please don't exceed six words.", null=True, blank=True),
        ),
    ]
