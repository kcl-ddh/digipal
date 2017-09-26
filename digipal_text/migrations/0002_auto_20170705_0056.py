# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digipal_text', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entryhand',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='textannotation',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='textcontent',
            name='languages',
            field=models.ManyToManyField(related_name='text_contents', to='digipal.Language', blank=True),
        ),
        migrations.AlterField(
            model_name='textcontent',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='textcontenttype',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='textcontentxml',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='textcontentxmlcopy',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='textcontentxmlstatus',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='textpattern',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
