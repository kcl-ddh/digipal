from haystack import indexes
import datetime
from models import Hand, Idiograph, Allograph, Scribe, HistoricalItem
from models import Character, Feature, Component, ItemPart, CurrentItem
from models import Repository, Place, IdiographComponent
import urllib


"""
Due to the disposition of the data being faceted (much of it contains spaces),
all facet fields are being url-encoded during the preparation step:
    prepare_currentitem_exact()

This means that the auto_query narrow() methods in FacetForm.search() must be
passed url-encoded strings, and that values must be un-quoted for display in
the template. This is accomplished by using a custom template filter:
    unquote_string
"""

class HandIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for hands """
    text = indexes.CharField(document=True, use_template=True)

    assigneddate = indexes.CharField(
        model_attr='assigned_date',
        faceted=True,
        null=True)
    assignedplace = indexes.CharField(
        model_attr="assigned_place",
        faceted=True,
        null=True)
    currentitem = indexes.CharField(
        model_attr="item_part__current_item__display_label",
        faceted=True,
        null=True)
    historicalitem = indexes.CharField(
        model_attr="item_part__historical_item__display_label",
        faceted=True,
        null=True)
    scribe = indexes.CharField(
        model_attr="scribe",
        faceted=True,
        null=True)
    idiograph = indexes.MultiValueField(
        model_attr="idiographs",
        faceted=True,
        null=True)
    allograph = indexes.CharField(
        faceted=True,
        null=True)
    character = indexes.CharField(
        faceted=True,
        null=True)

    modifieddate = indexes.DateTimeField(model_attr='modified', null=True)

    def get_model(self):
        return Hand

    def prepare_assigneddate_exact(self, obj):
        if obj.assigned_date:
            return urllib.quote(obj.assigned_date.date.encode('utf-8'))

    def prepare_assignedplace_exact(self, obj):
        if obj.assigned_place:
            return urllib.quote(obj.assigned_place.name.encode('utf-8'))

    # def prepare_currentitem_exact(self, obj):
    #     return
    #         obj.item_part.current_item.display_label.encode

    def prepare_historicalitem_exact(self, obj):
        return urllib.quote(
            obj.item_part.historical_item.display_label.encode('utf-8'))

    def prepare_scribe_exact(self, obj):
        if obj.scribe:
            return obj.scribe.name

    def prepare_idiograph_exact(self, obj):
        results = []
        if obj.idiographs():
            for idios in obj.idiographs():
                split_labels = idios.split()
                results.append('-'.join(token for token in split_labels))
        return results



    # def prepare_idiograph_exact(self, obj):
    #     results = []
    #     if obj.scribe:
    #         for idiograph in obj.scribe.idiograph_set.all():
    #             if isinstance(idiograph.display_label, unicode):
    #                 # leave as is
    #                 results.append(idiograph.display_label)
    #             else:
    #                 # decode utf-8 to unicode
    #                 results.append(idiograph.display_label.decode('utf8'))
    #     return results

    def prepare_allograph_exact(self, obj):
        results = []
        if obj.scribe:
            for idiograph in obj.scribe.idiographs.all():
                if isinstance(idiograph.allograph.name, unicode):
                    # encode as utf-8
                    results.append(idiograph.allograph.name.encode('utf8'))
                else:
                    # decode utf-8
                    results.append(idiograph.allograph.name.decode('utf8'))
        return results

    def prepare_character_exact(self, obj):
        results = []
        if obj.scribe:
            for idiograph in obj.scribe.idiographs.all():
                if isinstance(idiograph.allograph.character.name, unicode):
                    # encode as utf-8
                    results.append(idiograph.allograph.character.name.encode('utf8'))
                else:
                    # decode utf-8
                    results.append(idiograph.allograph.character.name.decode('utf8'))
        return results

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class CurrentItemIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for Current Items """
    text = indexes.CharField(document=True, use_template=True)

    repository = indexes.CharField(model_attr="repository", faceted=True)
    repository_place = indexes.CharField(
        model_attr="repository__place",
        null=True,
        faceted=True)
    shelfmark = indexes.CharField(model_attr="shelfmark", faceted=True)
    description = indexes.CharField(model_attr="description", null=True)
    display_label = indexes.CharField(model_attr="display_label")
    modified_date = indexes.DateTimeField(model_attr='modified')

    def get_model(self):
        return CurrentItem

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class IdiographIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for idiographs """
    text = indexes.CharField(document=True, use_template=True)

    allograph = indexes.CharField(model_attr="allograph")
    scribe = indexes.CharField(model_attr='scribe', null=True)
    aspects = indexes.CharField(model_attr="aspects", null=True)
    modified_date = indexes.DateTimeField(model_attr='modified')

    def get_model(self):
        return Idiograph

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class AllographIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for allographs """
    text = indexes.CharField(document=True, use_template=True)

    name = indexes.CharField(model_attr="name")
    character = indexes.CharField(model_attr="character")
    aspects = indexes.CharField(model_attr="aspects", null=True)
    modified_date = indexes.DateTimeField(model_attr="modified")

    def get_model(self):
        return Allograph

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class CharacterIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for characters """
    text = indexes.CharField(document=True, use_template=True)

    name = indexes.CharField(model_attr="name")
    form = indexes.CharField(model_attr="form")
    ontograph = indexes.CharField(model_attr="ontograph")
    components = indexes.CharField(model_attr="components")
    modified_date = indexes.DateTimeField(model_attr="modified")

    def get_model(self):
        return Character

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class ScribeIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for Scribes """
    text = indexes.CharField(document=True, use_template=True)

    name = indexes.CharField(model_attr='name')
    scriptorium = indexes.CharField(
        model_attr="scriptorium", null=True)
    modified_date = indexes.DateTimeField(model_attr='modified')

    def get_model(self):
        return Scribe

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class ItemPartIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for Item Parts """
    text = indexes.CharField(document=True, use_template=True)

    historical_item = indexes.CharField(model_attr="historical_item")
    current_item = indexes.CharField(model_attr="current_item")
    locus = indexes.CharField(model_attr="locus", null=True)
    modified_date = indexes.DateTimeField(model_attr='modified')

    def get_model(self):
        return ItemPart

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class HistoricalItemIndex(indexes.SearchIndex, indexes.Indexable):
    """ Searching for Historical Items """
    text = indexes.CharField(document=True, use_template=True)

    historical_item_type = indexes.CharField(model_attr='historical_item_type')
    historical_item_format = indexes.CharField(
        model_attr='historical_item_format', null=True)
    date = indexes.CharField(
        model_attr="date", null=True)
    histitem_name = indexes.CharField(
        model_attr="name", null=True)
    catalogue_number = indexes.CharField(
        model_attr="catalogue_number")
    modified_date = indexes.DateTimeField(model_attr='modified')

    def get_model(self):
        return HistoricalItem

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class FeatureIndex(indexes.SearchIndex, indexes.Indexable):
    """ """
    text = indexes.CharField(document=True, use_template=True)

    feature_name = indexes.CharField(model_attr="name")
    modified_date = indexes.DateTimeField(model_attr='modified')

    def get_model(self):
        return Feature

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class ComponentIndex(indexes.SearchIndex, indexes.Indexable):
    """ """
    text = indexes.CharField(document=True, use_template=True)

    component_name = indexes.CharField(model_attr="name")
    features = indexes.CharField(model_attr="features")
    modified_date = indexes.DateTimeField(model_attr='modified')


    def get_model(self):
        return Component

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class RepositoryIndex(indexes.SearchIndex, indexes.Indexable):
    """ """
    text = indexes.CharField(document=True, use_template=True)

    repository_name = indexes.CharField(model_attr="name", faceted=True)
    short_name = indexes.CharField(model_attr="short_name", null=True)
    place = indexes.CharField(model_attr="place", faceted=True)
    modified_date = indexes.DateTimeField(model_attr='modified')


    def get_model(self):
        return Repository

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())


class PlaceIndex(indexes.SearchIndex, indexes.Indexable):
    """ """
    text = indexes.CharField(document=True, use_template=True)

    place_name = indexes.CharField(model_attr="name", faceted=True)
    region = indexes.CharField(model_attr="name", faceted=True)
    modified_date = indexes.DateTimeField(model_attr='modified')


    def get_model(self):
        return Place

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            modified__lte=datetime.datetime.now())
