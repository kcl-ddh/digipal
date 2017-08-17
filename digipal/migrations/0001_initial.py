# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import iipimage.storage
from mezzanine.conf import settings
import tinymce.models
import iipimage.fields
import digipal.iipfield.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Allograph',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('default', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False,
                                               help_text="If ticked the public users won't see this allograph on the web site.")),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['character__ontograph__sort_order', 'character__ontograph__ontograph_type__name', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AllographComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('allograph', models.ForeignKey(
                    related_name=b'allograph_components', to='digipal.Allograph')),
            ],
            options={
                'ordering': ['allograph', 'component'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Alphabet',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('cutout', models.CharField(default=None,
                                            max_length=256, null=True, blank=True)),
                ('rotation', models.FloatField(default=0.0)),
                ('vector_id', models.TextField(default='', blank=True)),
                ('geo_json', models.TextField()),
                ('display_note', tinymce.models.HTMLField(
                    help_text=b'An optional note that will be publicly visible on the website.', null=True, blank=True)),
                ('internal_note', tinymce.models.HTMLField(
                    help_text=b'An optional note for internal or editorial purpose only. Will not be visible on the website.', null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('holes', models.CharField(max_length=1000, null=True, blank=True)),
                ('clientid', models.CharField(db_index=True,
                                              max_length=24, null=True, blank=True)),
                ('type', models.CharField(default=None, max_length=15,
                                          null=True, db_index=True, blank=True)),
                ('after', models.ForeignKey(related_name=b'allograph_after',
                                            blank=True, to='digipal.Allograph', null=True)),
                ('author', models.ForeignKey(
                    editable=False, to=settings.AUTH_USER_MODEL)),
                ('before', models.ForeignKey(related_name=b'allograph_before',
                                             blank=True, to='digipal.Allograph', null=True)),
            ],
            options={
                'ordering': ['graph', 'modified'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ApiTransform',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(
                    help_text=b'A unique title for this XSLT template.', unique=True, max_length=30)),
                ('slug', models.SlugField(help_text=b'A unique code to refer to this template when using the web API. @xslt=slug',
                                          unique=True, max_length=30, editable=False)),
                ('template', models.TextField(
                    help_text=b'Your XSLT template', null=True, blank=True)),
                ('description', models.TextField(
                    help_text=b'A description of the transform', null=True, blank=True)),
                ('mimetype', models.CharField(default=b'text/xml',
                                              help_text=b'The mime type of the output from the transform.', max_length=30)),
                ('sample_request', models.CharField(default=b'graph', max_length=200, null=True,
                                                    help_text=b'A sample API request this transform can be tested on. It is a API request URL without this part: http://.../digipal/api/. E.g. graph/100,101,102?@select=id,str', blank=True)),
                ('webpage', models.BooleanField(
                    default=False, verbose_name=b'Show as a webpage?')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Appearance',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('text', models.CharField(max_length=128)),
                ('sort_order', models.IntegerField()),
                ('description', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['sort_order', 'text'],
                'verbose_name_plural': 'Appearance',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('dubitable', models.NullBooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['historical_item'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Aspect',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AuthenticityCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CarouselItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('link', models.CharField(help_text=b'The URL of the page this item links to. E.g. /digipal/page/80/',
                                          max_length=200, null=True, blank=True)),
                ('image_file', models.ImageField(default=None, upload_to=b'uploads/images/', blank=True,
                                                 help_text=b'The image for this item. Not needed if you have provided a the URL of the image in the image field.', null=True)),
                ('image', models.CharField(help_text=b'The URL of the image of this item. E.g. /static/digipal/images/Catholic_Homilies.jpg. Not needed if you have uploaded a file in the image_file field.', max_length=200, null=True, blank=True)),
                ('image_alt', models.CharField(
                    help_text=b'a few words describing the image content.', max_length=300, null=True, blank=True)),
                ('image_title', models.CharField(
                    help_text=b'the piece of text that appears when the user moved the mouse over the image (optional).', max_length=300, null=True, blank=True)),
                ('sort_order', models.IntegerField(
                    help_text=b'The order of this item in the carousel. 1 appears first, 2 second, etc. 0 is hidden.')),
                ('title', models.CharField(
                    help_text=b'The caption under the image of this item. This can contain some inline HTML. You can surround some text with just <a>...</a>.', max_length=300)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CatalogueNumber',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=100)),
                ('number_slug', models.SlugField(
                    max_length=100, null=True, blank=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['source', 'number'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('sort_order', models.PositiveIntegerField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('unicode_point', models.CharField(
                    max_length=32, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['ontograph__sort_order', 'ontograph__ontograph_type__name', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CharacterForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Collation',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('fragment', models.NullBooleanField()),
                ('leaves', models.IntegerField(null=True, blank=True)),
                ('front_flyleaves', models.IntegerField(null=True, blank=True)),
                ('back_flyleaves', models.IntegerField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['historical_item'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ComponentFeature',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('set_by_default', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('component', models.ForeignKey(to='digipal.Component')),
            ],
            options={
                'ordering': ['component__name', 'feature__name'],
                'db_table': 'digipal_component_features',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='County',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Counties',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CurrentItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('shelfmark', models.CharField(max_length=128)),
                ('description', models.TextField(null=True, blank=True)),
                ('display_label', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['repository', 'shelfmark'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Date',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('date', models.CharField(max_length=128)),
                ('sort_order', models.IntegerField(null=True, blank=True)),
                ('weight', models.FloatField()),
                ('band', models.IntegerField(null=True, blank=True)),
                ('additional_band', models.IntegerField(null=True, blank=True)),
                ('post_conquest', models.NullBooleanField()),
                ('s_xi', models.NullBooleanField()),
                ('min_weight', models.FloatField(null=True, blank=True)),
                ('max_weight', models.FloatField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('legacy_reference', models.CharField(
                    default=b'', max_length=128, null=True, blank=True)),
                ('evidence', models.CharField(default=b'',
                                              max_length=255, null=True, blank=True)),
            ],
            options={
                'ordering': ['sort_order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DateEvidence',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('is_firm_date', models.BooleanField(default=False)),
                ('date_description', models.CharField(
                    max_length=128, null=True, blank=True)),
                ('evidence', models.TextField(default=b'',
                                              max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('date', models.ForeignKey(blank=True, to='digipal.Date', null=True)),
            ],
            options={
                'ordering': ['date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Decoration',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('illustrated', models.NullBooleanField()),
                ('decorated', models.NullBooleanField()),
                ('illuminated', models.NullBooleanField()),
                ('num_colours', models.IntegerField(null=True, blank=True)),
                ('colours', models.CharField(max_length=256, null=True, blank=True)),
                ('num_inks', models.IntegerField(null=True, blank=True)),
                ('inks', models.CharField(max_length=256, null=True, blank=True)),
                ('style', models.CharField(max_length=256, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('catalogue_references', models.CharField(
                    max_length=256, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['historical_item'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Description',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('description', tinymce.models.HTMLField(null=True, blank=True)),
                ('comments', models.TextField(null=True, blank=True)),
                ('summary', models.CharField(max_length=256, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['historical_item', 'text'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=32)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Format',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Graph',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('display_label', models.CharField(
                    max_length=256, editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('aspects', models.ManyToManyField(
                    to='digipal.Aspect', null=True, blank=True)),
                ('group', models.ForeignKey(related_name=b'parts', blank=True, to='digipal.Graph',
                                            help_text='Select a graph that contains this one', null=True)),
            ],
            options={
                'ordering': ['idiograph'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GraphComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('component', models.ForeignKey(to='digipal.Component')),
                ('features', models.ManyToManyField(to='digipal.Feature')),
                ('graph', models.ForeignKey(
                    related_name=b'graph_components', to='digipal.Graph')),
            ],
            options={
                'ordering': ['graph', 'component'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Hair',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('label', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['label'],
                'verbose_name_plural': 'Hair',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Hand',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('num', models.IntegerField(
                    help_text=b'The order of display of the Hand label. e.g. 1 for Main Hand, 2 for Gloss.')),
                ('scragg', models.CharField(max_length=6, null=True, blank=True)),
                ('ker', models.CharField(max_length=10, null=True, blank=True)),
                ('em_title', models.CharField(max_length=256, null=True, blank=True)),
                ('label', models.TextField(null=True, blank=True)),
                ('display_note', models.TextField(
                    help_text=b'An optional note that will be publicly visible on the website.', null=True, blank=True)),
                ('internal_note', models.TextField(
                    help_text=b'An optional note for internal or editorial purpose only. Will not be visible on the website.', null=True, blank=True)),
                ('relevant', models.NullBooleanField()),
                ('latin_only', models.NullBooleanField()),
                ('gloss_only', models.NullBooleanField()),
                ('membra_disjecta', models.NullBooleanField()),
                ('num_glosses', models.IntegerField(null=True, blank=True)),
                ('num_glossing_hands', models.IntegerField(null=True, blank=True)),
                ('scribble_only', models.NullBooleanField()),
                ('imitative', models.NullBooleanField()),
                ('comments', models.TextField(null=True, blank=True)),
                ('display_label', models.CharField(
                    max_length=128, editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('locus', models.CharField(default=b'',
                                           max_length=300, null=True, blank=True)),
                ('surrogates', models.CharField(
                    default=b'', max_length=50, null=True, blank=True)),
                ('selected_locus', models.CharField(
                    default=b'', max_length=100, null=True, blank=True)),
                ('appearance', models.ForeignKey(
                    blank=True, to='digipal.Appearance', null=True)),
                ('assigned_date', models.ForeignKey(
                    blank=True, to='digipal.Date', null=True)),
            ],
            options={
                'ordering': ['item_part', 'num'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HandDescription',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(
                    help_text=b'This field accepts TEI elements.')),
                ('label', models.CharField(
                    help_text=b"A label assigned to this hand by a source. E.g. 'Alpha' (for source 'Flight').", max_length=64, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('hand', models.ForeignKey(related_name=b'descriptions',
                                           blank=True, to='digipal.Hand', null=True)),
            ],
            options={
                'ordering': ['hand', 'source__priority'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoricalItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('date', models.CharField(max_length=128, null=True, blank=True)),
                ('date_sort', models.CharField(
                    help_text=b'Optional date, usually narrower than the date field. Used for result visualisation and sorting.', max_length=128, null=True, blank=True)),
                ('name', models.CharField(max_length=256, null=True, blank=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('vernacular', models.NullBooleanField()),
                ('neumed', models.NullBooleanField()),
                ('catalogue_number', models.CharField(
                    max_length=128, editable=False)),
                ('display_label', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('legacy_reference', models.CharField(
                    default=b'', max_length=128, null=True, blank=True)),
                ('categories', models.ManyToManyField(
                    to='digipal.Category', null=True, blank=True)),
                ('hair', models.ForeignKey(blank=True, to='digipal.Hair', null=True)),
                ('historical_item_format', models.ForeignKey(
                    blank=True, to='digipal.Format', null=True)),
            ],
            options={
                'ordering': ['display_label', 'date', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoricalItemDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('evidence', models.TextField()),
                ('vernacular', models.NullBooleanField()),
                ('addition', models.NullBooleanField()),
                ('dubitable', models.NullBooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('date', models.ForeignKey(to='digipal.Date')),
                ('historical_item', models.ForeignKey(to='digipal.HistoricalItem')),
            ],
            options={
                'ordering': ['date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoricalItemType',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Idiograph',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('display_label', models.CharField(
                    max_length=128, editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('allograph', models.ForeignKey(to='digipal.Allograph')),
                ('aspects', models.ManyToManyField(
                    to='digipal.Aspect', null=True, blank=True)),
            ],
            options={
                'ordering': ['allograph'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IdiographComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('component', models.ForeignKey(to='digipal.Component')),
                ('features', models.ManyToManyField(to='digipal.Feature')),
                ('idiograph', models.ForeignKey(to='digipal.Idiograph')),
            ],
            options={
                'ordering': ['idiograph', 'component'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('keywords_string', models.CharField(
                    max_length=500, editable=False, blank=True)),
                ('locus', models.CharField(default=b'', max_length=64, blank=True)),
                ('folio_side', models.CharField(
                    max_length=4, null=True, blank=True)),
                ('folio_number', models.CharField(
                    max_length=8, null=True, blank=True)),
                ('caption', models.CharField(max_length=256, null=True, blank=True)),
                ('image', models.ImageField(null=True,
                                            upload_to=b'uploads/images/', blank=True)),
                ('iipimage', iipimage.fields.ImageField(storage=iipimage.storage.ImageStorage(
                ), max_length=200, null=True, upload_to=digipal.iipfield.storage.get_image_path, blank=True)),
                ('display_label', models.CharField(max_length=128)),
                ('custom_label', models.CharField(
                    help_text=b'Leave blank unless you want to customise the value of the display label field', max_length=128, null=True, blank=True)),
                ('transcription', models.TextField(null=True, blank=True)),
                ('internal_notes', models.TextField(null=True, blank=True)),
                ('width', models.IntegerField(default=0)),
                ('height', models.IntegerField(default=0)),
                ('size', models.IntegerField(default=0)),
                ('quire', models.CharField(default=None, max_length=10,
                                           null=True, help_text=b'A quire number, e.g. 3', blank=True)),
                ('page_boundaries', models.CharField(default=None, max_length=100, null=True,
                                                     help_text=b'relative coordinates of the page boundaries in json. e.g. [[0.3, 0.1], [0.7, 0.9]]', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['item_part__display_label', 'folio_number', 'folio_side'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImageAnnotationStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Image annotation statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=256)),
                ('foundation', models.CharField(
                    max_length=128, null=True, blank=True)),
                ('refoundation', models.CharField(
                    max_length=128, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InstitutionType',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemOrigin',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('evidence', models.TextField(default=b'', null=True, blank=True)),
                ('dubitable', models.NullBooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('historical_item', models.ForeignKey(to='digipal.HistoricalItem')),
                ('institution', models.ForeignKey(related_name=b'item_origins',
                                                  blank=True, to='digipal.Institution', null=True)),
            ],
            options={
                'ordering': ['historical_item'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemPart',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('keywords_string', models.CharField(
                    max_length=500, editable=False, blank=True)),
                ('group_locus', models.CharField(
                    help_text=b'the locus of this part in the group', max_length=64, null=True, blank=True)),
                ('locus', models.CharField(default=b'face', max_length=64, null=True,
                                           help_text=b'the location of this part in the Current Item', blank=True)),
                ('display_label', models.CharField(max_length=300)),
                ('pagination', models.BooleanField(default=False)),
                ('notes', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('current_item', models.ForeignKey(default=None,
                                                   blank=True, to='digipal.CurrentItem', null=True)),
                ('group', models.ForeignKey(related_name=b'subdivisions', blank=True,
                                            to='digipal.ItemPart', help_text=b'the item part which contains this one', null=True)),
            ],
            options={
                'ordering': ['display_label'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemPartAuthenticity',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(default=None, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('category', models.ForeignKey(
                    related_name=b'itempart_authenticity', to='digipal.AuthenticityCategory')),
                ('item_part', models.ForeignKey(
                    related_name=b'authenticities', to='digipal.ItemPart')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemPartItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('locus', models.CharField(default=b'', max_length=64, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('historical_item', models.ForeignKey(
                    related_name=b'partitions', to='digipal.HistoricalItem')),
                ('item_part', models.ForeignKey(
                    related_name=b'constitutionalities', to='digipal.ItemPart')),
            ],
            options={
                'ordering': ['historical_item__id'],
                'verbose_name': 'Item Partition',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemPartType',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KeyVal',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=300)),
                ('val', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['key'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LatinStyle',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('style', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['style'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Layout',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('page_height', models.IntegerField(null=True, blank=True)),
                ('page_width', models.IntegerField(null=True, blank=True)),
                ('frame_height', models.IntegerField(null=True, blank=True)),
                ('frame_width', models.IntegerField(null=True, blank=True)),
                ('tramline_width', models.IntegerField(null=True, blank=True)),
                ('lines', models.IntegerField(null=True, blank=True)),
                ('columns', models.IntegerField(null=True, blank=True)),
                ('on_top_line', models.NullBooleanField()),
                ('multiple_sheet_rulling', models.NullBooleanField()),
                ('bilinear_ruling', models.NullBooleanField()),
                ('comments', models.TextField(null=True, blank=True)),
                ('insular_pricking', models.NullBooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('hair_arrangement', models.ForeignKey(
                    blank=True, to='digipal.Hair', null=True)),
                ('historical_item', models.ForeignKey(
                    blank=True, to='digipal.HistoricalItem', null=True)),
                ('item_part', models.ForeignKey(related_name=b'layouts',
                                                blank=True, to='digipal.ItemPart', null=True)),
            ],
            options={
                'ordering': ['item_part', 'historical_item'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('label', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['label'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MediaPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(
                    help_text=b'A short label describing the type of permission. For internal use only.', max_length=64)),
                ('permission', models.IntegerField(default=100, choices=[
                 (100, b'Private'), (200, b'Thumbnail Only'), (300, b'Full Resolution')])),
                ('display_message', tinymce.models.HTMLField(
                    default=b'', help_text=b'This message will be displayed when the image is not available to the user.', blank=True)),
            ],
            options={
                'ordering': ['label'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Ontograph',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('nesting_level', models.IntegerField(
                    default=0, help_text=b'An ontograph can contain another ontograph of a higher level. E.g. level 3 con be made of ontographs of level 4 and above. Set 0 to prevent any nesting.')),
                ('sort_order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'ontograph_type__name', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OntographType',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Owner',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('date', models.CharField(max_length=128)),
                ('display_label', models.CharField(
                    default=b'', max_length=250, blank=True)),
                ('evidence', models.TextField()),
                ('rebound', models.NullBooleanField()),
                ('annotated', models.NullBooleanField()),
                ('dubitable', models.NullBooleanField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('institution', models.ForeignKey(related_name=b'owners', default=None, blank=True, to='digipal.Institution',
                                                  help_text=b'Please select either an institution or a person. Deprecated, please use `Repository` instead.', null=True)),
            ],
            options={
                'ordering': ['date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OwnerType',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=256)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=256)),
                ('other_names', models.CharField(
                    max_length=256, null=True, blank=True)),
                ('eastings', models.FloatField(null=True, blank=True)),
                ('northings', models.FloatField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('current_county', models.ForeignKey(
                    related_name=b'county_current', blank=True, to='digipal.County', null=True)),
                ('historical_county', models.ForeignKey(
                    related_name=b'county_historical', blank=True, to='digipal.County', null=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlaceEvidence',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('written_as', models.CharField(
                    max_length=128, null=True, blank=True)),
                ('place_description', models.CharField(
                    max_length=128, null=True, blank=True)),
                ('evidence', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('hand', models.ForeignKey(default=None,
                                           blank=True, to='digipal.Hand', null=True)),
                ('historical_item', models.ForeignKey(default=None,
                                                      blank=True, to='digipal.HistoricalItem', null=True)),
                ('place', models.ForeignKey(to='digipal.Place')),
            ],
            options={
                'ordering': ['place'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlaceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Proportion',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('cue_height', models.FloatField()),
                ('value', models.FloatField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('hand', models.ForeignKey(to='digipal.Hand')),
                ('measurement', models.ForeignKey(to='digipal.Measurement')),
            ],
            options={
                'ordering': ['hand', 'measurement'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=128)),
                ('name_index', models.CharField(
                    max_length=1, null=True, blank=True)),
                ('legacy_reference', models.CharField(
                    default=b'', max_length=128, null=True, blank=True)),
                ('full_reference', tinymce.models.HTMLField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=256)),
                ('short_name', models.CharField(
                    max_length=64, null=True, blank=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('comma', models.NullBooleanField()),
                ('british_isles', models.NullBooleanField()),
                ('digital_project', models.NullBooleanField()),
                ('copyright_notice', tinymce.models.HTMLField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('media_permission', models.ForeignKey(default=None, blank=True, to='digipal.MediaPermission',
                                                       help_text=b'The default permission scheme for images originating\n            from this repository.<br/> The Pages can override the\n            repository default permission.\n            ', null=True)),
                ('part_of', models.ForeignKey(related_name=b'parts',
                                              default=None, blank=True, to='digipal.Repository', null=True)),
                ('place', models.ForeignKey(to='digipal.Place')),
                ('type', models.ForeignKey(related_name=b'repositories',
                                           default=None, blank=True, to='digipal.OwnerType', null=True)),
            ],
            options={
                'ordering': ['short_name', 'name'],
                'verbose_name_plural': 'Repositories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('request', models.CharField(default=b'',
                                             max_length=300, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('result_count', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Scribe',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('date', models.CharField(max_length=128, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('legacy_reference', models.CharField(
                    default=b'', max_length=128, null=True, blank=True)),
                ('reference', models.ManyToManyField(
                    to='digipal.Reference', null=True, blank=True)),
                ('scriptorium', models.ForeignKey(
                    blank=True, to='digipal.Institution', null=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=128)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('allographs', models.ManyToManyField(to='digipal.Allograph')),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ScriptComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('component', models.ForeignKey(to='digipal.Component')),
                ('features', models.ManyToManyField(to='digipal.Feature')),
                ('script', models.ForeignKey(to='digipal.Script')),
            ],
            options={
                'ordering': ['script', 'component'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(
                    help_text=b'Full reference of this source (e.g. British Library)', unique=True, max_length=128)),
                ('label', models.CharField(help_text=b'A shorthand for the reference (e.g. BL)',
                                           max_length=30, unique=True, null=True, blank=True)),
                ('label_slug', models.SlugField(
                    max_length=30, null=True, blank=True)),
                ('label_styled', models.CharField(
                    help_text=b'Styled version of the label, text between _underscores_ will be italicised', max_length=30, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('priority', models.IntegerField(
                    default=0, help_text='Lower number has a higher display priority on the web site. 0 is top, 1 second, then 2, etc.')),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=32)),
                ('default', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Status',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StewartRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('scragg', models.CharField(default=b'',
                                            max_length=300, null=True, blank=True)),
                ('repository', models.CharField(default=b'',
                                                max_length=300, null=True, blank=True)),
                ('shelf_mark', models.CharField(default=b'',
                                                max_length=300, null=True, blank=True)),
                ('stokes_db', models.CharField(default=b'',
                                               max_length=300, null=True, blank=True)),
                ('fols', models.CharField(default=b'',
                                          max_length=300, null=True, blank=True)),
                ('gneuss', models.CharField(default=b'',
                                            max_length=300, null=True, blank=True)),
                ('ker', models.CharField(default=b'',
                                         max_length=300, null=True, blank=True)),
                ('sp', models.CharField(default=b'',
                                        max_length=300, null=True, blank=True)),
                ('ker_hand', models.CharField(default=b'',
                                              max_length=300, null=True, blank=True)),
                ('locus', models.CharField(default=b'',
                                           max_length=300, null=True, blank=True)),
                ('selected', models.CharField(default=b'',
                                              max_length=300, null=True, blank=True)),
                ('adate', models.CharField(default=b'',
                                           max_length=300, null=True, blank=True)),
                ('location', models.CharField(default=b'',
                                              max_length=300, null=True, blank=True)),
                ('surrogates', models.CharField(default=b'',
                                                max_length=300, null=True, blank=True)),
                ('contents', models.CharField(default=b'',
                                              max_length=500, null=True, blank=True)),
                ('notes', models.CharField(default=b'',
                                           max_length=600, null=True, blank=True)),
                ('em', models.CharField(default=b'',
                                        max_length=800, null=True, blank=True)),
                ('glosses', models.CharField(default=b'',
                                             max_length=300, null=True, blank=True)),
                ('minor', models.CharField(default=b'',
                                           max_length=300, null=True, blank=True)),
                ('charter', models.CharField(default=b'',
                                             max_length=300, null=True, blank=True)),
                ('cartulary', models.CharField(default=b'',
                                               max_length=300, null=True, blank=True)),
                ('eel', models.CharField(default=b'',
                                         max_length=1000, null=True, blank=True)),
                ('import_messages', models.TextField(
                    default=b'', null=True, blank=True)),
                ('matched_hands', models.CharField(
                    default=b'', max_length=1000, null=True, blank=True)),
            ],
            options={
                'ordering': ['scragg'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
                ('date', models.CharField(max_length=128, null=True, blank=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('categories', models.ManyToManyField(related_name=b'texts',
                                                      null=True, to='digipal.Category', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Text Info',
                'verbose_name_plural': 'Text Info',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextItemPart',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('locus', models.CharField(max_length=20, null=True, blank=True)),
                ('date', models.CharField(max_length=128, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(
                    auto_now=True, auto_now_add=True)),
                ('item_part', models.ForeignKey(
                    related_name=b'text_instances', to='digipal.ItemPart')),
                ('text', models.ForeignKey(
                    related_name=b'text_instances', to='digipal.Text')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='textitempart',
            unique_together=set([('item_part', 'text')]),
        ),
        migrations.AddField(
            model_name='text',
            name='item_parts',
            field=models.ManyToManyField(
                related_name=b'texts', through='digipal.TextItemPart', to='digipal.ItemPart'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='languages',
            field=models.ManyToManyField(
                related_name=b'texts', null=True, to='digipal.Language', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='text',
            unique_together=set([('name',)]),
        ),
        migrations.AlterUniqueTogether(
            name='reference',
            unique_together=set([('name', 'name_index')]),
        ),
        migrations.AddField(
            model_name='placeevidence',
            name='reference',
            field=models.ForeignKey(to='digipal.Reference'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='region',
            field=models.ForeignKey(
                blank=True, to='digipal.Region', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='type',
            field=models.ForeignKey(
                blank=True, to='digipal.PlaceType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='owner',
            name='person',
            field=models.ForeignKey(related_name=b'owners', default=None, blank=True, to='digipal.Person',
                                    help_text=b'Please select either an institution or a person. Deprecated, please use `Repository` instead.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='owner',
            name='repository',
            field=models.ForeignKey(related_name=b'owners', default=None, blank=True, to='digipal.Repository',
                                    help_text=b'`Repository` actually represents the institution, person or library owning the item.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ontograph',
            name='ontograph_type',
            field=models.ForeignKey(
                verbose_name=b'type', to='digipal.OntographType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='ontograph',
            unique_together=set([('name', 'ontograph_type')]),
        ),
        migrations.AddField(
            model_name='itempartauthenticity',
            name='source',
            field=models.ForeignKey(
                related_name=b'itempart_authenticity', blank=True, to='digipal.Source', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='itempartauthenticity',
            unique_together=set([('item_part', 'category', 'source')]),
        ),
        migrations.AddField(
            model_name='itempart',
            name='historical_items',
            field=models.ManyToManyField(
                related_name=b'item_parts', through='digipal.ItemPartItem', to='digipal.HistoricalItem'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itempart',
            name='owners',
            field=models.ManyToManyField(
                to='digipal.Owner', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itempart',
            name='type',
            field=models.ForeignKey(
                blank=True, to='digipal.ItemPartType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemorigin',
            name='place',
            field=models.ForeignKey(
                related_name=b'item_origins', blank=True, to='digipal.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='institution',
            name='founder',
            field=models.ForeignKey(
                related_name=b'person_founder', blank=True, to='digipal.Person', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='institution',
            name='institution_type',
            field=models.ForeignKey(to='digipal.InstitutionType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='institution',
            name='patron',
            field=models.ForeignKey(
                related_name=b'person_patron', blank=True, to='digipal.Person', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='institution',
            name='place',
            field=models.ForeignKey(to='digipal.Place'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='institution',
            name='reformer',
            field=models.ForeignKey(
                related_name=b'person_reformer', blank=True, to='digipal.Person', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='annotation_status',
            field=models.ForeignKey(related_name=b'images', default=None,
                                    blank=True, to='digipal.ImageAnnotationStatus', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='item_part',
            field=models.ForeignKey(
                related_name=b'images', default=None, blank=True, to='digipal.ItemPart', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='media_permission',
            field=models.ForeignKey(default=None, blank=True, to='digipal.MediaPermission',
                                    help_text=b'This field determines if the image is publicly visible and the reason if not.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='idiograph',
            name='scribe',
            field=models.ForeignKey(
                related_name=b'idiographs', blank=True, to='digipal.Scribe', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalitem',
            name='historical_item_type',
            field=models.ForeignKey(to='digipal.HistoricalItemType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalitem',
            name='language',
            field=models.ForeignKey(
                blank=True, to='digipal.Language', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalitem',
            name='owners',
            field=models.ManyToManyField(
                to='digipal.Owner', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='handdescription',
            name='source',
            field=models.ForeignKey(
                related_name=b'hand_descriptions', blank=True, to='digipal.Source', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='assigned_place',
            field=models.ForeignKey(blank=True, to='digipal.Place', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='glossed_text',
            field=models.ForeignKey(
                blank=True, to='digipal.Category', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='images',
            field=models.ManyToManyField(help_text=b'Select the images this hand appears in. The list of available images comes from images connected to the Item Part associated to this Hand.',
                                         related_name=b'hands', null=True, to='digipal.Image', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='item_part',
            field=models.ForeignKey(
                related_name=b'hands', to='digipal.ItemPart'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='latin_style',
            field=models.ForeignKey(
                blank=True, to='digipal.LatinStyle', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='scribe',
            field=models.ForeignKey(
                related_name=b'hands', blank=True, to='digipal.Scribe', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='script',
            field=models.ForeignKey(
                blank=True, to='digipal.Script', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='hand',
            name='stewart_record',
            field=models.ForeignKey(
                related_name=b'hands', blank=True, to='digipal.StewartRecord', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='graph',
            name='hand',
            field=models.ForeignKey(related_name=b'graphs', to='digipal.Hand'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='graph',
            name='idiograph',
            field=models.ForeignKey(to='digipal.Idiograph'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='description',
            name='historical_item',
            field=models.ForeignKey(
                blank=True, to='digipal.HistoricalItem', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='description',
            name='source',
            field=models.ForeignKey(to='digipal.Source'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='description',
            name='text',
            field=models.ForeignKey(
                related_name=b'descriptions', blank=True, to='digipal.Text', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='description',
            unique_together=set([('source', 'historical_item', 'text')]),
        ),
        migrations.AddField(
            model_name='decoration',
            name='historical_item',
            field=models.ForeignKey(to='digipal.HistoricalItem'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dateevidence',
            name='hand',
            field=models.ForeignKey(
                default=None, blank=True, to='digipal.Hand', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dateevidence',
            name='historical_item',
            field=models.ForeignKey(related_name=b'date_evidences', default=None,
                                    blank=True, to='digipal.HistoricalItem', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dateevidence',
            name='reference',
            field=models.ForeignKey(
                blank=True, to='digipal.Reference', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='currentitem',
            name='owners',
            field=models.ManyToManyField(
                default=None, related_name=b'current_items', null=True, to='digipal.Owner', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='currentitem',
            name='repository',
            field=models.ForeignKey(to='digipal.Repository'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='currentitem',
            unique_together=set([('repository', 'shelfmark')]),
        ),
        migrations.AddField(
            model_name='componentfeature',
            name='feature',
            field=models.ForeignKey(to='digipal.Feature'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='componentfeature',
            unique_together=set([('component', 'feature')]),
        ),
        migrations.AddField(
            model_name='component',
            name='features',
            field=models.ManyToManyField(
                related_name=b'components', through='digipal.ComponentFeature', to='digipal.Feature'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collation',
            name='historical_item',
            field=models.ForeignKey(to='digipal.HistoricalItem'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='character',
            name='components',
            field=models.ManyToManyField(
                to='digipal.Component', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='character',
            name='form',
            field=models.ForeignKey(to='digipal.CharacterForm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='character',
            name='ontograph',
            field=models.ForeignKey(to='digipal.Ontograph'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cataloguenumber',
            name='historical_item',
            field=models.ForeignKey(related_name=b'catalogue_numbers',
                                    blank=True, to='digipal.HistoricalItem', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cataloguenumber',
            name='source',
            field=models.ForeignKey(to='digipal.Source'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cataloguenumber',
            name='text',
            field=models.ForeignKey(
                related_name=b'catalogue_numbers', blank=True, to='digipal.Text', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='cataloguenumber',
            unique_together=set(
                [('source', 'number', 'historical_item', 'text')]),
        ),
        migrations.AddField(
            model_name='aspect',
            name='features',
            field=models.ManyToManyField(to='digipal.Feature'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='archive',
            name='historical_item',
            field=models.ForeignKey(to='digipal.HistoricalItem'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='annotation',
            name='graph',
            field=models.OneToOneField(
                null=True, blank=True, to='digipal.Graph'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='annotation',
            name='image',
            field=models.ForeignKey(to='digipal.Image', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='annotation',
            name='status',
            field=models.ForeignKey(
                blank=True, to='digipal.Status', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alphabet',
            name='hands',
            field=models.ManyToManyField(
                to='digipal.Hand', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alphabet',
            name='ontographs',
            field=models.ManyToManyField(
                to='digipal.Ontograph', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allographcomponent',
            name='component',
            field=models.ForeignKey(to='digipal.Component'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allographcomponent',
            name='features',
            field=models.ManyToManyField(
                to='digipal.Feature', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allograph',
            name='aspects',
            field=models.ManyToManyField(
                to='digipal.Aspect', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allograph',
            name='character',
            field=models.ForeignKey(to='digipal.Character'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='allograph',
            unique_together=set([('name', 'character')]),
        ),
    ]
