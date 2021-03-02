# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0003_auto_20170717_2037'),
    ]

    operations = [
        migrations.AddField(
            model_name='itempart',
            name='custom_label',
            field=models.CharField(help_text=b'A custom label for this part. If blank the shelfmark will be used as a label.', max_length=300, null=True, blank=True),
        ),
    ]
