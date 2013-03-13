# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Appearance'
        db.create_table('digipal_appearance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Appearance'])

        # Adding model 'Feature'
        db.create_table('digipal_feature', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Feature'])

        # Adding model 'Component'
        db.create_table('digipal_component', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Component'])

        # Adding M2M table for field features on 'Component'
        db.create_table('digipal_component_features', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('component', models.ForeignKey(orm['digipal.component'], null=False)),
            ('feature', models.ForeignKey(orm['digipal.feature'], null=False))
        ))
        db.create_unique('digipal_component_features', ['component_id', 'feature_id'])

        # Adding model 'Aspect'
        db.create_table('digipal_aspect', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Aspect'])

        # Adding M2M table for field features on 'Aspect'
        db.create_table('digipal_aspect_features', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('aspect', models.ForeignKey(orm['digipal.aspect'], null=False)),
            ('feature', models.ForeignKey(orm['digipal.feature'], null=False))
        ))
        db.create_unique('digipal_aspect_features', ['aspect_id', 'feature_id'])

        # Adding model 'OntographType'
        db.create_table('digipal_ontographtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['OntographType'])

        # Adding model 'Ontograph'
        db.create_table('digipal_ontograph', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('ontograph_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.OntographType'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Ontograph'])

        # Adding unique constraint on 'Ontograph', fields ['name', 'ontograph_type']
        db.create_unique('digipal_ontograph', ['name', 'ontograph_type_id'])

        # Adding model 'Character'
        db.create_table('digipal_character', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('unicode_point', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('form', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('ontograph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Ontograph'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Character'])

        # Adding M2M table for field components on 'Character'
        db.create_table('digipal_character_components', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('character', models.ForeignKey(orm['digipal.character'], null=False)),
            ('component', models.ForeignKey(orm['digipal.component'], null=False))
        ))
        db.create_unique('digipal_character_components', ['character_id', 'component_id'])

        # Adding model 'Allograph'
        db.create_table('digipal_allograph', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('character', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Character'])),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Allograph'])

        # Adding unique constraint on 'Allograph', fields ['name', 'character']
        db.create_unique('digipal_allograph', ['name', 'character_id'])

        # Adding M2M table for field aspects on 'Allograph'
        db.create_table('digipal_allograph_aspects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('allograph', models.ForeignKey(orm['digipal.allograph'], null=False)),
            ('aspect', models.ForeignKey(orm['digipal.aspect'], null=False))
        ))
        db.create_unique('digipal_allograph_aspects', ['allograph_id', 'aspect_id'])

        # Adding model 'AllographComponent'
        db.create_table('digipal_allographcomponent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('allograph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Allograph'])),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Component'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['AllographComponent'])

        # Adding M2M table for field features on 'AllographComponent'
        db.create_table('digipal_allographcomponent_features', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('allographcomponent', models.ForeignKey(orm['digipal.allographcomponent'], null=False)),
            ('feature', models.ForeignKey(orm['digipal.feature'], null=False))
        ))
        db.create_unique('digipal_allographcomponent_features', ['allographcomponent_id', 'feature_id'])

        # Adding model 'Script'
        db.create_table('digipal_script', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Script'])

        # Adding M2M table for field allographs on 'Script'
        db.create_table('digipal_script_allographs', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('script', models.ForeignKey(orm['digipal.script'], null=False)),
            ('allograph', models.ForeignKey(orm['digipal.allograph'], null=False))
        ))
        db.create_unique('digipal_script_allographs', ['script_id', 'allograph_id'])

        # Adding model 'ScriptComponent'
        db.create_table('digipal_scriptcomponent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('script', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Script'])),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Component'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['ScriptComponent'])

        # Adding M2M table for field features on 'ScriptComponent'
        db.create_table('digipal_scriptcomponent_features', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('scriptcomponent', models.ForeignKey(orm['digipal.scriptcomponent'], null=False)),
            ('feature', models.ForeignKey(orm['digipal.feature'], null=False))
        ))
        db.create_unique('digipal_scriptcomponent_features', ['scriptcomponent_id', 'feature_id'])

        # Adding model 'Reference'
        db.create_table('digipal_reference', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('name_index', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('legacy_reference', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('full_reference', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Reference'])

        # Adding unique constraint on 'Reference', fields ['name', 'name_index']
        db.create_unique('digipal_reference', ['name', 'name_index'])

        # Adding model 'Owner'
        db.create_table('digipal_owner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('date', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('evidence', self.gf('django.db.models.fields.TextField')()),
            ('rebound', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('annotated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('dubitable', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Owner'])

        # Adding model 'Date'
        db.create_table('digipal_date', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('weight', self.gf('django.db.models.fields.FloatField')()),
            ('band', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('additional_band', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('post_conquest', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('s_xi', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('min_weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('max_weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Date'])

        # Adding model 'Category'
        db.create_table('digipal_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('sort_order', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Category'])

        # Adding model 'Format'
        db.create_table('digipal_format', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Format'])

        # Adding model 'Hair'
        db.create_table('digipal_hair', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Hair'])

        # Adding model 'HistoricalItemType'
        db.create_table('digipal_historicalitemtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['HistoricalItemType'])

        # Adding model 'Language'
        db.create_table('digipal_language', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Language'])

        # Adding model 'HistoricalItem'
        db.create_table('digipal_historicalitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('historical_item_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItemType'])),
            ('historical_item_format', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Format'], null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('hair', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Hair'], null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Language'], null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('vernacular', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('neumed', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('catalogue_number', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('display_label', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['HistoricalItem'])

        # Adding M2M table for field categories on 'HistoricalItem'
        db.create_table('digipal_historicalitem_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('historicalitem', models.ForeignKey(orm['digipal.historicalitem'], null=False)),
            ('category', models.ForeignKey(orm['digipal.category'], null=False))
        ))
        db.create_unique('digipal_historicalitem_categories', ['historicalitem_id', 'category_id'])

        # Adding M2M table for field owners on 'HistoricalItem'
        db.create_table('digipal_historicalitem_owners', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('historicalitem', models.ForeignKey(orm['digipal.historicalitem'], null=False)),
            ('owner', models.ForeignKey(orm['digipal.owner'], null=False))
        ))
        db.create_unique('digipal_historicalitem_owners', ['historicalitem_id', 'owner_id'])

        # Adding model 'Source'
        db.create_table('digipal_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=12, unique=True, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Source'])

        # Adding model 'CatalogueNumber'
        db.create_table('digipal_cataloguenumber', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='catalogue_numbers', to=orm['digipal.HistoricalItem'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Source'])),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['CatalogueNumber'])

        # Adding unique constraint on 'CatalogueNumber', fields ['source', 'number']
        db.create_unique('digipal_cataloguenumber', ['source_id', 'number'])

        # Adding model 'Collation'
        db.create_table('digipal_collation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('fragment', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('leaves', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('front_flyleaves', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('back_flyleaves', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Collation'])

        # Adding model 'Decoration'
        db.create_table('digipal_decoration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('illustrated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('decorated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('illuminated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('num_colours', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('colours', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('num_inks', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('inks', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('style', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('catalogue_references', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Decoration'])

        # Adding model 'Description'
        db.create_table('digipal_description', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Source'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Description'])

        # Adding model 'Layout'
        db.create_table('digipal_layout', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('page_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('page_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('frame_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('frame_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('tramline_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('lines', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('columns', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('on_top_line', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('multiple_sheet_rulling', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('bilinear_ruling', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('comments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('hair_arrangement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Hair'], null=True, blank=True)),
            ('insular_pricking', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Layout'])

        # Adding model 'ItemOrigin'
        db.create_table('digipal_itemorigin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('evidence', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('dubitable', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['ItemOrigin'])

        # Adding model 'Archive'
        db.create_table('digipal_archive', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('dubitable', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Archive'])

        # Adding model 'Region'
        db.create_table('digipal_region', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Region'])

        # Adding model 'County'
        db.create_table('digipal_county', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['County'])

        # Adding model 'Place'
        db.create_table('digipal_place', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('eastings', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('northings', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Region'], null=True, blank=True)),
            ('current_county', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='county_current', null=True, to=orm['digipal.County'])),
            ('historical_county', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='county_historical', null=True, to=orm['digipal.County'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Place'])

        # Adding model 'Repository'
        db.create_table('digipal_repository', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Place'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('comma', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('british_isles', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('digital_project', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Repository'])

        # Adding model 'CurrentItem'
        db.create_table('digipal_currentitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Repository'])),
            ('shelfmark', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('display_label', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['CurrentItem'])

        # Adding unique constraint on 'CurrentItem', fields ['repository', 'shelfmark']
        db.create_unique('digipal_currentitem', ['repository_id', 'shelfmark'])

        # Adding model 'Person'
        db.create_table('digipal_person', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Person'])

        # Adding model 'InstitutionType'
        db.create_table('digipal_institutiontype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['InstitutionType'])

        # Adding model 'Institution'
        db.create_table('digipal_institution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('institution_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.InstitutionType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('founder', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='person_founder', null=True, to=orm['digipal.Person'])),
            ('reformer', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='person_reformer', null=True, to=orm['digipal.Person'])),
            ('patron', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='person_patron', null=True, to=orm['digipal.Person'])),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Place'])),
            ('foundation', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('refoundation', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Institution'])

        # Adding model 'Scribe'
        db.create_table('digipal_scribe', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('date', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('scriptorium', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Institution'], null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Scribe'])

        # Adding M2M table for field reference on 'Scribe'
        db.create_table('digipal_scribe_reference', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('scribe', models.ForeignKey(orm['digipal.scribe'], null=False)),
            ('reference', models.ForeignKey(orm['digipal.reference'], null=False))
        ))
        db.create_unique('digipal_scribe_reference', ['scribe_id', 'reference_id'])

        # Adding model 'Idiograph'
        db.create_table('digipal_idiograph', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('allograph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Allograph'])),
            ('scribe', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='idiographs', null=True, to=orm['digipal.Scribe'])),
            ('display_label', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Idiograph'])

        # Adding M2M table for field aspects on 'Idiograph'
        db.create_table('digipal_idiograph_aspects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('idiograph', models.ForeignKey(orm['digipal.idiograph'], null=False)),
            ('aspect', models.ForeignKey(orm['digipal.aspect'], null=False))
        ))
        db.create_unique('digipal_idiograph_aspects', ['idiograph_id', 'aspect_id'])

        # Adding model 'IdiographComponent'
        db.create_table('digipal_idiographcomponent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('idiograph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Idiograph'])),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Component'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['IdiographComponent'])

        # Adding M2M table for field features on 'IdiographComponent'
        db.create_table('digipal_idiographcomponent_features', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('idiographcomponent', models.ForeignKey(orm['digipal.idiographcomponent'], null=False)),
            ('feature', models.ForeignKey(orm['digipal.feature'], null=False))
        ))
        db.create_unique('digipal_idiographcomponent_features', ['idiographcomponent_id', 'feature_id'])

        # Adding model 'HistoricalItemDate'
        db.create_table('digipal_historicalitemdate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('date', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Date'])),
            ('evidence', self.gf('django.db.models.fields.TextField')()),
            ('vernacular', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('addition', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('dubitable', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['HistoricalItemDate'])

        # Adding model 'ItemPart'
        db.create_table('digipal_itempart', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('historical_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.HistoricalItem'])),
            ('current_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.CurrentItem'])),
            ('locus', self.gf('django.db.models.fields.CharField')(default='face', max_length=64, null=True, blank=True)),
            ('display_label', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['ItemPart'])

        # Adding unique constraint on 'ItemPart', fields ['historical_item', 'current_item', 'locus']
        db.create_unique('digipal_itempart', ['historical_item_id', 'current_item_id', 'locus'])

        # Adding model 'LatinStyle'
        db.create_table('digipal_latinstyle', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('style', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['LatinStyle'])

        # Adding model 'Page'
        db.create_table('digipal_page', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item_part', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pages', to=orm['digipal.ItemPart'])),
            ('locus', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('caption', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('display_label', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Page'])

        # Adding model 'Hand'
        db.create_table('digipal_hand', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('num', self.gf('django.db.models.fields.IntegerField')()),
            ('item_part', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.ItemPart'])),
            ('script', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Script'], null=True, blank=True)),
            ('scribe', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Scribe'], null=True, blank=True)),
            ('assigned_date', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Date'], null=True, blank=True)),
            ('assigned_place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Place'], null=True, blank=True)),
            ('scragg', self.gf('django.db.models.fields.CharField')(max_length=6, null=True, blank=True)),
            ('scragg_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('em_title', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('em_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('mancass_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('display_note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('internal_note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('appearance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Appearance'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('relevant', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('latin_only', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('gloss_only', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('membra_disjecta', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('num_glosses', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('num_glossing_hands', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('glossed_text', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Category'], null=True, blank=True)),
            ('scribble_only', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('imitative', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('latin_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.LatinStyle'], null=True, blank=True)),
            ('comments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('display_label', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Hand'])

        # Adding M2M table for field pages on 'Hand'
        db.create_table('digipal_hand_pages', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('hand', models.ForeignKey(orm['digipal.hand'], null=False)),
            ('page', models.ForeignKey(orm['digipal.page'], null=False))
        ))
        db.create_unique('digipal_hand_pages', ['hand_id', 'page_id'])

        # Adding model 'Alphabet'
        db.create_table('digipal_alphabet', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Alphabet'])

        # Adding M2M table for field ontographs on 'Alphabet'
        db.create_table('digipal_alphabet_ontographs', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('alphabet', models.ForeignKey(orm['digipal.alphabet'], null=False)),
            ('ontograph', models.ForeignKey(orm['digipal.ontograph'], null=False))
        ))
        db.create_unique('digipal_alphabet_ontographs', ['alphabet_id', 'ontograph_id'])

        # Adding M2M table for field hands on 'Alphabet'
        db.create_table('digipal_alphabet_hands', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('alphabet', models.ForeignKey(orm['digipal.alphabet'], null=False)),
            ('hand', models.ForeignKey(orm['digipal.hand'], null=False))
        ))
        db.create_unique('digipal_alphabet_hands', ['alphabet_id', 'hand_id'])

        # Adding model 'DateEvidence'
        db.create_table('digipal_dateevidence', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Hand'])),
            ('date', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Date'], null=True, blank=True)),
            ('date_description', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('reference', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Reference'], null=True, blank=True)),
            ('evidence', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['DateEvidence'])

        # Adding model 'Graph'
        db.create_table('digipal_graph', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('idiograph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Idiograph'])),
            ('hand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Hand'])),
            ('display_label', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Graph'])

        # Adding M2M table for field aspects on 'Graph'
        db.create_table('digipal_graph_aspects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('graph', models.ForeignKey(orm['digipal.graph'], null=False)),
            ('aspect', models.ForeignKey(orm['digipal.aspect'], null=False))
        ))
        db.create_unique('digipal_graph_aspects', ['graph_id', 'aspect_id'])

        # Adding model 'GraphComponent'
        db.create_table('digipal_graphcomponent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('graph', self.gf('django.db.models.fields.related.ForeignKey')(related_name='graph_components', to=orm['digipal.Graph'])),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Component'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['GraphComponent'])

        # Adding M2M table for field features on 'GraphComponent'
        db.create_table('digipal_graphcomponent_features', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('graphcomponent', models.ForeignKey(orm['digipal.graphcomponent'], null=False)),
            ('feature', models.ForeignKey(orm['digipal.feature'], null=False))
        ))
        db.create_unique('digipal_graphcomponent_features', ['graphcomponent_id', 'feature_id'])

        # Adding model 'Status'
        db.create_table('digipal_status', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Status'])

        # Adding model 'Annotation'
        db.create_table('digipal_annotation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Page'])),
            ('cutout', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Status'], null=True, blank=True)),
            ('before', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='allograph_before', null=True, to=orm['digipal.Allograph'])),
            ('graph', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['digipal.Graph'], unique=True, null=True, blank=True)),
            ('after', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='allograph_after', null=True, to=orm['digipal.Allograph'])),
            ('vector_id', self.gf('django.db.models.fields.TextField')()),
            ('geo_json', self.gf('django.db.models.fields.TextField')()),
            ('display_note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('internal_note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Annotation'])

        # Adding unique constraint on 'Annotation', fields ['page', 'vector_id']
        db.create_unique('digipal_annotation', ['page_id', 'vector_id'])

        # Adding model 'PlaceEvidence'
        db.create_table('digipal_placeevidence', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Hand'])),
            ('place', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Place'])),
            ('place_description', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('reference', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Reference'])),
            ('evidence', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['PlaceEvidence'])

        # Adding model 'Measurement'
        db.create_table('digipal_measurement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Measurement'])

        # Adding model 'Proportion'
        db.create_table('digipal_proportion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Hand'])),
            ('measurement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['digipal.Measurement'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('cue_height', self.gf('django.db.models.fields.FloatField')()),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('digipal', ['Proportion'])


    def backwards(self, orm):
        # Removing unique constraint on 'Annotation', fields ['page', 'vector_id']
        db.delete_unique('digipal_annotation', ['page_id', 'vector_id'])

        # Removing unique constraint on 'ItemPart', fields ['historical_item', 'current_item', 'locus']
        db.delete_unique('digipal_itempart', ['historical_item_id', 'current_item_id', 'locus'])

        # Removing unique constraint on 'CurrentItem', fields ['repository', 'shelfmark']
        db.delete_unique('digipal_currentitem', ['repository_id', 'shelfmark'])

        # Removing unique constraint on 'CatalogueNumber', fields ['source', 'number']
        db.delete_unique('digipal_cataloguenumber', ['source_id', 'number'])

        # Removing unique constraint on 'Reference', fields ['name', 'name_index']
        db.delete_unique('digipal_reference', ['name', 'name_index'])

        # Removing unique constraint on 'Allograph', fields ['name', 'character']
        db.delete_unique('digipal_allograph', ['name', 'character_id'])

        # Removing unique constraint on 'Ontograph', fields ['name', 'ontograph_type']
        db.delete_unique('digipal_ontograph', ['name', 'ontograph_type_id'])

        # Deleting model 'Appearance'
        db.delete_table('digipal_appearance')

        # Deleting model 'Feature'
        db.delete_table('digipal_feature')

        # Deleting model 'Component'
        db.delete_table('digipal_component')

        # Removing M2M table for field features on 'Component'
        db.delete_table('digipal_component_features')

        # Deleting model 'Aspect'
        db.delete_table('digipal_aspect')

        # Removing M2M table for field features on 'Aspect'
        db.delete_table('digipal_aspect_features')

        # Deleting model 'OntographType'
        db.delete_table('digipal_ontographtype')

        # Deleting model 'Ontograph'
        db.delete_table('digipal_ontograph')

        # Deleting model 'Character'
        db.delete_table('digipal_character')

        # Removing M2M table for field components on 'Character'
        db.delete_table('digipal_character_components')

        # Deleting model 'Allograph'
        db.delete_table('digipal_allograph')

        # Removing M2M table for field aspects on 'Allograph'
        db.delete_table('digipal_allograph_aspects')

        # Deleting model 'AllographComponent'
        db.delete_table('digipal_allographcomponent')

        # Removing M2M table for field features on 'AllographComponent'
        db.delete_table('digipal_allographcomponent_features')

        # Deleting model 'Script'
        db.delete_table('digipal_script')

        # Removing M2M table for field allographs on 'Script'
        db.delete_table('digipal_script_allographs')

        # Deleting model 'ScriptComponent'
        db.delete_table('digipal_scriptcomponent')

        # Removing M2M table for field features on 'ScriptComponent'
        db.delete_table('digipal_scriptcomponent_features')

        # Deleting model 'Reference'
        db.delete_table('digipal_reference')

        # Deleting model 'Owner'
        db.delete_table('digipal_owner')

        # Deleting model 'Date'
        db.delete_table('digipal_date')

        # Deleting model 'Category'
        db.delete_table('digipal_category')

        # Deleting model 'Format'
        db.delete_table('digipal_format')

        # Deleting model 'Hair'
        db.delete_table('digipal_hair')

        # Deleting model 'HistoricalItemType'
        db.delete_table('digipal_historicalitemtype')

        # Deleting model 'Language'
        db.delete_table('digipal_language')

        # Deleting model 'HistoricalItem'
        db.delete_table('digipal_historicalitem')

        # Removing M2M table for field categories on 'HistoricalItem'
        db.delete_table('digipal_historicalitem_categories')

        # Removing M2M table for field owners on 'HistoricalItem'
        db.delete_table('digipal_historicalitem_owners')

        # Deleting model 'Source'
        db.delete_table('digipal_source')

        # Deleting model 'CatalogueNumber'
        db.delete_table('digipal_cataloguenumber')

        # Deleting model 'Collation'
        db.delete_table('digipal_collation')

        # Deleting model 'Decoration'
        db.delete_table('digipal_decoration')

        # Deleting model 'Description'
        db.delete_table('digipal_description')

        # Deleting model 'Layout'
        db.delete_table('digipal_layout')

        # Deleting model 'ItemOrigin'
        db.delete_table('digipal_itemorigin')

        # Deleting model 'Archive'
        db.delete_table('digipal_archive')

        # Deleting model 'Region'
        db.delete_table('digipal_region')

        # Deleting model 'County'
        db.delete_table('digipal_county')

        # Deleting model 'Place'
        db.delete_table('digipal_place')

        # Deleting model 'Repository'
        db.delete_table('digipal_repository')

        # Deleting model 'CurrentItem'
        db.delete_table('digipal_currentitem')

        # Deleting model 'Person'
        db.delete_table('digipal_person')

        # Deleting model 'InstitutionType'
        db.delete_table('digipal_institutiontype')

        # Deleting model 'Institution'
        db.delete_table('digipal_institution')

        # Deleting model 'Scribe'
        db.delete_table('digipal_scribe')

        # Removing M2M table for field reference on 'Scribe'
        db.delete_table('digipal_scribe_reference')

        # Deleting model 'Idiograph'
        db.delete_table('digipal_idiograph')

        # Removing M2M table for field aspects on 'Idiograph'
        db.delete_table('digipal_idiograph_aspects')

        # Deleting model 'IdiographComponent'
        db.delete_table('digipal_idiographcomponent')

        # Removing M2M table for field features on 'IdiographComponent'
        db.delete_table('digipal_idiographcomponent_features')

        # Deleting model 'HistoricalItemDate'
        db.delete_table('digipal_historicalitemdate')

        # Deleting model 'ItemPart'
        db.delete_table('digipal_itempart')

        # Deleting model 'LatinStyle'
        db.delete_table('digipal_latinstyle')

        # Deleting model 'Page'
        db.delete_table('digipal_page')

        # Deleting model 'Hand'
        db.delete_table('digipal_hand')

        # Removing M2M table for field pages on 'Hand'
        db.delete_table('digipal_hand_pages')

        # Deleting model 'Alphabet'
        db.delete_table('digipal_alphabet')

        # Removing M2M table for field ontographs on 'Alphabet'
        db.delete_table('digipal_alphabet_ontographs')

        # Removing M2M table for field hands on 'Alphabet'
        db.delete_table('digipal_alphabet_hands')

        # Deleting model 'DateEvidence'
        db.delete_table('digipal_dateevidence')

        # Deleting model 'Graph'
        db.delete_table('digipal_graph')

        # Removing M2M table for field aspects on 'Graph'
        db.delete_table('digipal_graph_aspects')

        # Deleting model 'GraphComponent'
        db.delete_table('digipal_graphcomponent')

        # Removing M2M table for field features on 'GraphComponent'
        db.delete_table('digipal_graphcomponent_features')

        # Deleting model 'Status'
        db.delete_table('digipal_status')

        # Deleting model 'Annotation'
        db.delete_table('digipal_annotation')

        # Deleting model 'PlaceEvidence'
        db.delete_table('digipal_placeevidence')

        # Deleting model 'Measurement'
        db.delete_table('digipal_measurement')

        # Deleting model 'Proportion'
        db.delete_table('digipal_proportion')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'digipal.allograph': {
            'Meta': {'ordering': "['character__name', 'name']", 'unique_together': "(['name', 'character'],)", 'object_name': 'Allograph'},
            'aspects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Aspect']", 'null': 'True', 'blank': 'True'}),
            'character': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Character']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'digipal.allographcomponent': {
            'Meta': {'ordering': "['allograph', 'component']", 'object_name': 'AllographComponent'},
            'allograph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Allograph']"}),
            'component': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Component']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Feature']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.alphabet': {
            'Meta': {'ordering': "['name']", 'object_name': 'Alphabet'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hands': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Hand']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'ontographs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Ontograph']", 'null': 'True', 'blank': 'True'})
        },
        'digipal.annotation': {
            'Meta': {'ordering': "['graph', 'modified']", 'unique_together': "(('page', 'vector_id'),)", 'object_name': 'Annotation'},
            'after': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'allograph_after'", 'null': 'True', 'to': "orm['digipal.Allograph']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'before': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'allograph_before'", 'null': 'True', 'to': "orm['digipal.Allograph']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'cutout': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'display_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'geo_json': ('django.db.models.fields.TextField', [], {}),
            'graph': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['digipal.Graph']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Page']"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Status']", 'null': 'True', 'blank': 'True'}),
            'vector_id': ('django.db.models.fields.TextField', [], {})
        },
        'digipal.appearance': {
            'Meta': {'ordering': "['sort_order', 'text']", 'object_name': 'Appearance'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'digipal.archive': {
            'Meta': {'ordering': "['historical_item']", 'object_name': 'Archive'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dubitable': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'digipal.aspect': {
            'Meta': {'ordering': "['name']", 'object_name': 'Aspect'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['digipal.Feature']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.cataloguenumber': {
            'Meta': {'ordering': "['source', 'number']", 'unique_together': "(['source', 'number'],)", 'object_name': 'CatalogueNumber'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'catalogue_numbers'", 'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Source']"})
        },
        'digipal.category': {
            'Meta': {'ordering': "['name']", 'object_name': 'Category'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'digipal.character': {
            'Meta': {'ordering': "['name']", 'object_name': 'Character'},
            'components': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['digipal.Component']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'form': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'ontograph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Ontograph']"}),
            'unicode_point': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        },
        'digipal.collation': {
            'Meta': {'ordering': "['historical_item']", 'object_name': 'Collation'},
            'back_flyleaves': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fragment': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'front_flyleaves': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'leaves': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.component': {
            'Meta': {'ordering': "['name']", 'object_name': 'Component'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'components'", 'symmetrical': 'False', 'to': "orm['digipal.Feature']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.county': {
            'Meta': {'ordering': "['name']", 'object_name': 'County'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.currentitem': {
            'Meta': {'ordering': "['repository', 'shelfmark']", 'unique_together': "(['repository', 'shelfmark'],)", 'object_name': 'CurrentItem'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'display_label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Repository']"}),
            'shelfmark': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'digipal.date': {
            'Meta': {'ordering': "['sort_order']", 'object_name': 'Date'},
            'additional_band': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'band': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'max_weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'min_weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'post_conquest': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            's_xi': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {})
        },
        'digipal.dateevidence': {
            'Meta': {'ordering': "['date']", 'object_name': 'DateEvidence'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Date']", 'null': 'True', 'blank': 'True'}),
            'date_description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'hand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Hand']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Reference']", 'null': 'True', 'blank': 'True'})
        },
        'digipal.decoration': {
            'Meta': {'ordering': "['historical_item']", 'object_name': 'Decoration'},
            'catalogue_references': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'colours': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'decorated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'illuminated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'illustrated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'inks': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'num_colours': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_inks': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'style': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'digipal.description': {
            'Meta': {'ordering': "['historical_item']", 'object_name': 'Description'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Source']"})
        },
        'digipal.feature': {
            'Meta': {'ordering': "['name']", 'object_name': 'Feature'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        },
        'digipal.format': {
            'Meta': {'ordering': "['name']", 'object_name': 'Format'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.graph': {
            'Meta': {'ordering': "['idiograph']", 'object_name': 'Graph'},
            'aspects': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['digipal.Aspect']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_label': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'hand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Hand']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idiograph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Idiograph']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.graphcomponent': {
            'Meta': {'ordering': "['graph', 'component']", 'object_name': 'GraphComponent'},
            'component': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Component']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['digipal.Feature']", 'symmetrical': 'False'}),
            'graph': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'graph_components'", 'to': "orm['digipal.Graph']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.hair': {
            'Meta': {'ordering': "['label']", 'object_name': 'Hair'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.hand': {
            'Meta': {'ordering': "['display_label']", 'object_name': 'Hand'},
            'appearance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Appearance']", 'null': 'True', 'blank': 'True'}),
            'assigned_date': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Date']", 'null': 'True', 'blank': 'True'}),
            'assigned_place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Place']", 'null': 'True', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'display_label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'display_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'em_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'em_title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'gloss_only': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'glossed_text': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Category']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imitative': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'internal_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'item_part': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.ItemPart']"}),
            'label': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'latin_only': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'latin_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.LatinStyle']", 'null': 'True', 'blank': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mancass_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'membra_disjecta': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {}),
            'num_glosses': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_glossing_hands': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Page']", 'null': 'True', 'blank': 'True'}),
            'relevant': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'scragg': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'scragg_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'scribble_only': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'scribe': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Scribe']", 'null': 'True', 'blank': 'True'}),
            'script': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Script']", 'null': 'True', 'blank': 'True'})
        },
        'digipal.historicalitem': {
            'Meta': {'ordering': "['display_label', 'date', 'name']", 'object_name': 'HistoricalItem'},
            'catalogue_number': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Category']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'display_label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'hair': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Hair']", 'null': 'True', 'blank': 'True'}),
            'historical_item_format': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Format']", 'null': 'True', 'blank': 'True'}),
            'historical_item_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItemType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Language']", 'null': 'True', 'blank': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'neumed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Owner']", 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'vernacular': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'digipal.historicalitemdate': {
            'Meta': {'ordering': "['date']", 'object_name': 'HistoricalItemDate'},
            'addition': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Date']"}),
            'dubitable': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.TextField', [], {}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'vernacular': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'digipal.historicalitemtype': {
            'Meta': {'ordering': "['name']", 'object_name': 'HistoricalItemType'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'digipal.idiograph': {
            'Meta': {'ordering': "['allograph']", 'object_name': 'Idiograph'},
            'allograph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Allograph']"}),
            'aspects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Aspect']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'scribe': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'idiographs'", 'null': 'True', 'to': "orm['digipal.Scribe']"})
        },
        'digipal.idiographcomponent': {
            'Meta': {'ordering': "['idiograph', 'component']", 'object_name': 'IdiographComponent'},
            'component': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Component']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['digipal.Feature']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idiograph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Idiograph']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.institution': {
            'Meta': {'ordering': "['name']", 'object_name': 'Institution'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'foundation': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'founder': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'person_founder'", 'null': 'True', 'to': "orm['digipal.Person']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.InstitutionType']"}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'patron': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'person_patron'", 'null': 'True', 'to': "orm['digipal.Person']"}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Place']"}),
            'reformer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'person_reformer'", 'null': 'True', 'to': "orm['digipal.Person']"}),
            'refoundation': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'digipal.institutiontype': {
            'Meta': {'ordering': "['name']", 'object_name': 'InstitutionType'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'digipal.itemorigin': {
            'Meta': {'ordering': "['historical_item']", 'object_name': 'ItemOrigin'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dubitable': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'digipal.itempart': {
            'Meta': {'ordering': "['display_label']", 'unique_together': "(['historical_item', 'current_item', 'locus'],)", 'object_name': 'ItemPart'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.CurrentItem']"}),
            'display_label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locus': ('django.db.models.fields.CharField', [], {'default': "'face'", 'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.language': {
            'Meta': {'ordering': "['name']", 'object_name': 'Language'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.latinstyle': {
            'Meta': {'ordering': "['style']", 'object_name': 'LatinStyle'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'style': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'digipal.layout': {
            'Meta': {'ordering': "['historical_item']", 'object_name': 'Layout'},
            'bilinear_ruling': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'columns': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'frame_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'frame_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hair_arrangement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Hair']", 'null': 'True', 'blank': 'True'}),
            'historical_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.HistoricalItem']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'insular_pricking': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'lines': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'multiple_sheet_rulling': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'on_top_line': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'page_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'page_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tramline_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'digipal.measurement': {
            'Meta': {'ordering': "['label']", 'object_name': 'Measurement'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.ontograph': {
            'Meta': {'ordering': "['ontograph_type', 'name']", 'unique_together': "(['name', 'ontograph_type'],)", 'object_name': 'Ontograph'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ontograph_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.OntographType']"})
        },
        'digipal.ontographtype': {
            'Meta': {'ordering': "['name']", 'object_name': 'OntographType'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.owner': {
            'Meta': {'ordering': "['date']", 'object_name': 'Owner'},
            'annotated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'dubitable': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'rebound': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'digipal.page': {
            'Meta': {'ordering': "['display_label']", 'object_name': 'Page'},
            'caption': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'display_label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'item_part': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': "orm['digipal.ItemPart']"}),
            'locus': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'digipal.person': {
            'Meta': {'ordering': "['name']", 'object_name': 'Person'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        },
        'digipal.place': {
            'Meta': {'ordering': "['name']", 'object_name': 'Place'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_county': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'county_current'", 'null': 'True', 'to': "orm['digipal.County']"}),
            'eastings': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'historical_county': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'county_historical'", 'null': 'True', 'to': "orm['digipal.County']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'northings': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Region']", 'null': 'True', 'blank': 'True'})
        },
        'digipal.placeevidence': {
            'Meta': {'ordering': "['place']", 'object_name': 'PlaceEvidence'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'evidence': ('django.db.models.fields.TextField', [], {}),
            'hand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Hand']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Place']"}),
            'place_description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Reference']"})
        },
        'digipal.proportion': {
            'Meta': {'ordering': "['hand', 'measurement']", 'object_name': 'Proportion'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'cue_height': ('django.db.models.fields.FloatField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Hand']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'measurement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Measurement']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'digipal.reference': {
            'Meta': {'ordering': "['name']", 'unique_together': "(['name', 'name_index'],)", 'object_name': 'Reference'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'full_reference': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'legacy_reference': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name_index': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'})
        },
        'digipal.region': {
            'Meta': {'ordering': "['name']", 'object_name': 'Region'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.repository': {
            'Meta': {'ordering': "['name']", 'object_name': 'Repository'},
            'british_isles': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'comma': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'digital_project': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Place']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'digipal.scribe': {
            'Meta': {'ordering': "['name']", 'object_name': 'Scribe'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'reference': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Reference']", 'null': 'True', 'blank': 'True'}),
            'scriptorium': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Institution']", 'null': 'True', 'blank': 'True'})
        },
        'digipal.script': {
            'Meta': {'ordering': "['name']", 'object_name': 'Script'},
            'allographs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['digipal.Allograph']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'digipal.scriptcomponent': {
            'Meta': {'ordering': "['script', 'component']", 'object_name': 'ScriptComponent'},
            'component': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Component']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['digipal.Feature']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'script': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['digipal.Script']"})
        },
        'digipal.source': {
            'Meta': {'ordering': "['name']", 'object_name': 'Source'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '12', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'digipal.status': {
            'Meta': {'ordering': "['name']", 'object_name': 'Status'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        }
    }

    complete_apps = ['digipal']