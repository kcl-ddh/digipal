# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Page.folio_side'
        db.add_column('digipal_page', 'folio_side',
                      self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Page.folio_number'
        db.add_column('digipal_page', 'folio_number',
                      self.gf('django.db.models.fields.CharField')(max_length=8, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Page.iipimage'
        db.add_column('digipal_page', 'iipimage',
                      self.gf('iipimage.fields.ImageField')(max_length=100, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Page.folio_side'
        db.delete_column('digipal_page', 'folio_side')

        # Deleting field 'Page.folio_number'
        db.delete_column('digipal_page', 'folio_number')

        # Deleting field 'Page.iipimage'
        db.delete_column('digipal_page', 'iipimage')


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
            'components': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['digipal.Component']", 'null': 'True', 'blank': 'True'}),
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
            'folio_number': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'folio_side': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iipimage': ('iipimage.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
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
            'copyright_notice': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
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