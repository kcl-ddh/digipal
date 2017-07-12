# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import iipimage.storage
import iipimage.fields
import digipal.iipfield.storage


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0002_auto_20170705_0056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='iipimage',
            field=iipimage.fields.ImageField(storage=iipimage.storage.ImageStorage(base_url=b'https://mofa-images.dighum.kcl.ac.uk/iip/iipsrv.fcgi', location=b'/home/jeff/src/grph/digipal/mofa'), max_length=200, null=True, upload_to=digipal.iipfield.storage.get_image_path, blank=True),
        ),
    ]
