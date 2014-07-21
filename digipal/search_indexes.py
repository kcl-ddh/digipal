import datetime
from haystack import indexes
from digipal.models import Image


class ImageIndex(indexes.SearchIndex, indexes.Indexable):
    '''Haystack Index class for the Image model '''
    # full text
    text = indexes.CharField(document=True, use_template=True)
    
    #title = indexes.CharField(model_attr='display_label')
    
    # facets
    # CI
    place = indexes.CharField(model_attr='item_part__current_item__repository__place__name', faceted=True)
    #repo_name = indexes.CharField(model_attr='item_part__current_item__repository__name', faceted=True)
    # HI
    #index = indexes.MultiValueField(faceted=True)
    #ms_date = indexes.CharField(faceted=True)
    #index = indexes.DateTimeField(model_attr='pub_date')

    def get_model(self):
        return Image

    def prepare_repo_place2(self, obj):
        ret = obj.item_part.current_item.repository.place.name
        print ret
        return ret
    
    def prepare_index(self, obj):
        ret = [unicode(cn) for cn in obj.item_part.historical_item.catalogue_numbers.all()]
        return ret

    def prepare_ms_date(self, obj):
        return obj.item_part.historical_item.date        

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    