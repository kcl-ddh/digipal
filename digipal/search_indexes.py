import datetime
from haystack import indexes
from digipal.models import Image


class ImageIndex(indexes.SearchIndex, indexes.Indexable):
    print 'h1'
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='display_label')
    #repo_city = indexes.CharField(model_attr='user')
    #repo_name = indexes.CharField(model_attr='user')
    #index = indexes.DateTimeField(model_attr='pub_date')

    def get_model(self):
        return Image

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    