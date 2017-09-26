# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('digipal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntryHand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entry_number', models.CharField(max_length=20, db_index=True)),
                ('hand_label', models.CharField(max_length=20, db_index=True)),
                ('order', models.IntegerField(default=0, db_index=True)),
                ('correction', models.BooleanField(default=False, db_index=True)),
                ('certainty', models.FloatField(default=1.0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
                ('item_part', models.ForeignKey(related_name=b'entry_hands', to='digipal.ItemPart')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('elementid', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
                ('annotation', models.ForeignKey(related_name=b'textannotations', to='digipal.Annotation')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
                ('item_part', models.ForeignKey(related_name=b'text_contents', to='digipal.ItemPart')),
                ('languages', models.ManyToManyField(related_name=b'text_contents', null=True, to='digipal.Language', blank=True)),
                ('text', models.ForeignKey(related_name=b'text_contents', blank=True, to='digipal.Text', null=True)),
            ],
            options={
                'verbose_name': 'Text (meta)',
                'verbose_name_plural': 'Texts (meta)',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextContentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Text Type',
                'verbose_name_plural': 'Text Types',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextContentXML',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
                ('last_image', models.ForeignKey(related_name=b'text_content_xmls', blank=True, to='digipal.Image', null=True)),
            ],
            options={
                'verbose_name': 'Text (XML)',
                'verbose_name_plural': 'Texts (XML)',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextContentXMLCopy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ahash', models.CharField(max_length=100, null=True, blank=True)),
                ('content', models.BinaryField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
                ('source', models.ForeignKey(related_name=b'versions', blank=True, to='digipal_text.TextContentXML', null=True)),
            ],
            options={
                'verbose_name': 'Text Copy',
                'verbose_name_plural': 'Text Copies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextContentXMLStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
                ('sort_order', models.IntegerField(default=0, help_text=b'The order of this status in your workflow.')),
            ],
            options={
                'verbose_name': 'Text Status',
                'verbose_name_plural': 'Text Statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextPattern',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=100)),
                ('key', models.SlugField(unique=True, max_length=100)),
                ('pattern', models.CharField(max_length=1000, null=True, blank=True)),
                ('order', models.IntegerField(default=0, db_index=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['order', 'key'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='textpattern',
            unique_together=set([('key',)]),
        ),
        migrations.AlterUniqueTogether(
            name='textcontentxmlcopy',
            unique_together=set([('source', 'ahash')]),
        ),
        migrations.AddField(
            model_name='textcontentxml',
            name='status',
            field=models.ForeignKey(related_name=b'text_content_xmls', to='digipal_text.TextContentXMLStatus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='textcontentxml',
            name='text_content',
            field=models.ForeignKey(related_name=b'text_content_xmls', to='digipal_text.TextContent'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='textcontentxml',
            unique_together=set([('text_content',)]),
        ),
        migrations.AddField(
            model_name='textcontent',
            name='type',
            field=models.ForeignKey(related_name=b'text_contents', to='digipal_text.TextContentType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='textcontent',
            unique_together=set([('item_part', 'type')]),
        ),
        migrations.AlterUniqueTogether(
            name='textannotation',
            unique_together=set([('annotation', 'elementid')]),
        ),
        migrations.AlterUniqueTogether(
            name='entryhand',
            unique_together=set([('item_part', 'entry_number', 'hand_label', 'order', 'correction')]),
        ),
    ]
