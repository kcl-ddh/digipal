from digipal.models import Annotation, Graph
from django.db.models.signals import post_delete
from django.db import transaction

'''JIRA DIGIPAL-523: Check orphan graph records.
   Make sure the graph records won't survive without an annotation.
   Without this event, deleting an image or an annotation 
   would leave orphan graph records.
'''

@transaction.atomic
def post_delete_annotation(sender, **kwargs):
    annotation = kwargs['instance']
    
    try:
        if annotation and annotation.graph:
            annotation.graph.delete()
    except Graph.DoesNotExist, e:
        # The graph has already been deleted.
        # This shouldn't happen but we just ignore it.
        pass

def init_signals():
    post_delete.connect(post_delete_annotation, sender=Annotation, dispatch_uid="digipal.signals.annotation.post_delete")
